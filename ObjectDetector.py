import tensorrt as trt
import torch
import torchvision
import numpy as np
import cv2
import json
from pathlib import Path

class SettingsManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance.load_settings()
        return cls._instance

    def load_settings(self):
        try:
            config_path = Path("assets/config/settings.json")
            with open(config_path, "r") as f:
                self.settings = json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.settings = {}

    def get(self, key_path, default=None):
        keys = key_path.split('.')
        value = self.settings
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

settings_manager = SettingsManager()

class FastObjectDetector:
    def __init__(self, engine_path):
        self.logger = trt.Logger(trt.Logger.WARNING)
        self.device = torch.device('cuda')
        
        # Load TRT Engine
        self.engine = self._load_engine(engine_path)
        self.context = self.engine.create_execution_context()
        
        # Allocate buffers using PyTorch (Zero-Copy)
        self.inputs, self.outputs, self.bindings = self._allocate_buffers()
        
        self.model_input_size = (640, 640)
        
        # Output configuration
        output_tensor_name = self.engine.get_tensor_name(self.engine.num_io_tensors - 1)
        self.output_shape = self.engine.get_tensor_shape(output_tensor_name)
        
        # Warmup
        self._warmup_engine()

    def _load_engine(self, engine_path):
        with open(engine_path, 'rb') as f:
            runtime = trt.Runtime(self.logger)
            return runtime.deserialize_cuda_engine(f.read())

    def _allocate_buffers(self):
        inputs = []
        outputs = []
        bindings = []
        
        for i in range(self.engine.num_io_tensors):
            name = self.engine.get_tensor_name(i)
            shape = self.engine.get_tensor_shape(name)
            
            # Create PyTorch tensor on GPU
            # We use float32 for everything to match TRT default
            size = trt.volume(shape)
            dtype = torch.float32 
            
            # Allocate memory on GPU
            tensor = torch.zeros(tuple(shape), dtype=dtype, device=self.device)
            
            # Append the memory address (pointer) to bindings
            bindings.append(int(tensor.data_ptr()))
            
            if self.engine.get_tensor_mode(name) == trt.TensorIOMode.INPUT:
                inputs.append({'tensor': tensor, 'name': name})
            else:
                outputs.append({'tensor': tensor, 'name': name})
                
        return inputs, outputs, bindings

    def _warmup_engine(self, num_warmup=10):
        # Create dummy input on GPU
        dummy = torch.zeros((1, 3, 640, 640), device=self.device)
        for _ in range(num_warmup):
            # Pass pointer directly
            self.context.set_tensor_address(self.inputs[0]['name'], int(dummy.data_ptr()))
            self.context.set_tensor_address(self.outputs[0]['name'], int(self.outputs[0]['tensor'].data_ptr()))
            self.context.execute_async_v3(stream_handle=torch.cuda.current_stream().cuda_stream)
        torch.cuda.synchronize()

    def preprocess(self, frame_numpy):
        """
        Performs all preprocessing on GPU using PyTorch.
        Input: numpy array (H, W, C) from BetterCam
        """
        # 1. Upload to GPU (This is the ONLY CPU->GPU copy in the whole pipeline)
        # We assume input is BGRA or BGR. 
        frame_tensor = torch.from_numpy(frame_numpy).to(self.device, non_blocking=True)
        
        # 2. Handle Channels (H, W, C) -> (C, H, W)
        # If input has 4 channels (BGRA), slice to 3 (BGR)
        if frame_tensor.shape[2] == 4:
            frame_tensor = frame_tensor[:, :, :3]
            
        # Swap BGR to RGB (if your model needs RGB) 
        # Note: frame_tensor is currently [H, W, 3] in BGR
        # Flip channels:
        frame_tensor = frame_tensor.flip(2)
        
        # Permute to [C, H, W]
        frame_tensor = frame_tensor.permute(2, 0, 1)

        # 3. Add batch dimension -> [1, C, H, W] and convert to float
        frame_tensor = frame_tensor.unsqueeze(0).float()
        
        # 4. Normalize (0-255 -> 0.0-1.0)
        frame_tensor /= 255.0
        
        # 5. Resize using GPU Interpolation
        # This replaces cv2.resize and is MUCH faster
        frame_tensor = torch.nn.functional.interpolate(
            frame_tensor, 
            size=self.model_input_size, 
            mode='bilinear', 
            align_corners=False
        )
        
        return frame_tensor

    def detect(self, frame_numpy):
        # --- GPU PRE-PROCESSING ---
        input_tensor = self.preprocess(frame_numpy)
        
        # --- INFERENCE ---
        # Update input tensor address (in case PyTorch moved it, though unlikely)
        self.context.set_tensor_address(self.inputs[0]['name'], int(input_tensor.data_ptr()))
        self.context.set_tensor_address(self.outputs[0]['name'], int(self.outputs[0]['tensor'].data_ptr()))
        
        # Run inference using Torch's current CUDA stream
        self.context.execute_async_v3(stream_handle=torch.cuda.current_stream().cuda_stream)
        
        # --- GPU POST-PROCESSING ---
        return self._process_output_gpu(self.outputs[0]['tensor'])

    def _process_output_gpu(self, output_tensor):
        CONFIDENCE_THRESHOLD = settings_manager.get("AI.confidence", 0.65)
        NMS_IOU_THRESHOLD = settings_manager.get("AI.nms_iou_threshold", 0.3)

        # Output shape is likely [1, 5+classes, 8400] or [1, 8400, 5+classes]
        # We need to standardize to [N, 5+classes]
        
        # If shape is [1, 5, 8400], transpose it
        if output_tensor.shape[1] < output_tensor.shape[2]:
            output_tensor = output_tensor.transpose(1, 2)
            
        # Remove batch dim -> [8400, 5]
        prediction = output_tensor[0]
        
        # Columns: [x, y, w, h, score] (assuming class 0 only)
        # If multi-class, you'd take max class score, but let's assume single class/aimbot
        boxes_cxcywh = prediction[:, :4]
        scores = prediction[:, 4]

        # 1. Filter by confidence (GPU)
        mask = scores > CONFIDENCE_THRESHOLD
        
        # If nothing detected, return empty immediately
        if not mask.any():
            return []
            
        boxes_cxcywh = boxes_cxcywh[mask]
        scores = scores[mask]
        
        # 2. Convert xywh to xyxy (GPU)
        # x_c, y_c, w, h -> x1, y1, x2, y2
        xyxy = torch.zeros_like(boxes_cxcywh)
        xyxy[:, 0] = boxes_cxcywh[:, 0] - boxes_cxcywh[:, 2] / 2  # x1
        xyxy[:, 1] = boxes_cxcywh[:, 1] - boxes_cxcywh[:, 3] / 2  # y1
        xyxy[:, 2] = boxes_cxcywh[:, 0] + boxes_cxcywh[:, 2] / 2  # x2
        xyxy[:, 3] = boxes_cxcywh[:, 1] + boxes_cxcywh[:, 3] / 2  # y2
        
        # 3. NMS (GPU - Extremely Fast)
        keep_indices = torchvision.ops.nms(xyxy, scores, NMS_IOU_THRESHOLD)
        
        # Select final boxes
        final_boxes = xyxy[keep_indices]
        final_scores = scores[keep_indices]
        
        # 4. Move ONLY the final results to CPU
        # This is very small data (e.g., 1-2 boxes), so it's instant.
        final_boxes_cpu = final_boxes.cpu().numpy()
        final_scores_cpu = final_scores.cpu().numpy()
        
        results = []
        for i in range(len(final_boxes_cpu)):
            box = final_boxes_cpu[i]
            # Normalize coordinates back to 0-1 range for Main.py
            # They are currently in 0-640 range
            box[0] /= self.model_input_size[0]
            box[1] /= self.model_input_size[1]
            box[2] /= self.model_input_size[0]
            box[3] /= self.model_input_size[1]
            
            results.append({
                'bbox': box.tolist(),
                'confidence': float(final_scores_cpu[i]),
                'class_name': 'object'
            })
            
        return results

    def reload(self, engine_path):
        try:
            print(f"Reloading model from {engine_path}...")
            # Explicitly delete old objects to free GPU memory
            del self.context
            del self.engine
            del self.inputs
            del self.outputs
            torch.cuda.empty_cache()
            
            self.engine = self._load_engine(engine_path)
            self.context = self.engine.create_execution_context()
            self.inputs, self.outputs, self.bindings = self._allocate_buffers()
            
            output_tensor_name = self.engine.get_tensor_name(self.engine.num_io_tensors - 1)
            self.output_shape = self.engine.get_tensor_shape(output_tensor_name)
            
            self._warmup_engine()
            print("Model reload successful.")
            return True
        except Exception as e:
            print(f"Failed to reload model: {e}")
            return False

    def __del__(self):
        # Cleanup
        if hasattr(self, 'context'): del self.context
        if hasattr(self, 'engine'): del self.engine
        torch.cuda.empty_cache()