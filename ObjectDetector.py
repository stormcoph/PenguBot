import numpy as np
import tensorrt as trt
import pycuda.autoinit
import pycuda.driver as cuda
import cv2
import torch
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
            # Set global visual settings
            global detectionOverlay, fpsOverlay, fovOverlay
            detectionOverlay = self.settings["Visual"]["target"]
            fpsOverlay = self.settings["Visual"]["fps"]
            fovOverlay = self.settings["Visual"]["fov"]
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


# Initialize settings manager at module level
settings_manager = SettingsManager()

class FastObjectDetector:
    def __init__(self, engine_path):
        self.stream = cuda.Stream()
        self.logger = trt.Logger(trt.Logger.WARNING)
        self.engine = self._load_engine(engine_path)
        self.context = self.engine.create_execution_context()
        self.inputs, self.outputs, self.bindings = self._allocate_buffers()
        self.model_input_size = (640, 640)
        self.input_buffer = np.empty((1, 3, *self.model_input_size), dtype=np.float32)  # Pre-allocated buffer

        # Output configuration
        output_tensor_name = self.engine.get_tensor_name(self.engine.num_io_tensors - 1)
        self.output_shape = self.engine.get_tensor_shape(output_tensor_name)
        if len(self.output_shape) == 3:
            self.num_classes = 1
            self.num_outputs = self.output_shape[1]
            self.grid_cells = self.output_shape[2]
        else:
            raise ValueError(f"Unexpected output shape: {self.output_shape}")

        self._warmup_engine()

    def _load_engine(self, engine_path):
        with open(engine_path, 'rb') as f:
            runtime = trt.Runtime(self.logger)
            return runtime.deserialize_cuda_engine(f.read())

    def _allocate_buffers(self):
        inputs, outputs, bindings = [], [], []
        for binding in self.engine:
            shape = self.engine.get_tensor_shape(binding)
            size = trt.volume(shape)
            dtype = trt.nptype(self.engine.get_tensor_dtype(binding))
            host_mem = cuda.pagelocked_empty(size, dtype)
            device_mem = cuda.mem_alloc(host_mem.nbytes)
            bindings.append(int(device_mem))
            if self.engine.get_tensor_mode(binding) == trt.TensorIOMode.INPUT:
                inputs.append({'host': host_mem, 'device': device_mem, 'name': binding})
            else:
                outputs.append({'host': host_mem, 'device': device_mem, 'name': binding})
        return inputs, outputs, bindings

    def _warmup_engine(self, num_warmup=10):
        dummy_input = np.zeros((1, 3, 640, 640), dtype=np.float32)
        for _ in range(num_warmup):
            self.infer(dummy_input)
        torch.cuda.synchronize()

    def infer(self, input_tensor):
        np.copyto(self.inputs[0]['host'], input_tensor.ravel())
        cuda.memcpy_htod_async(self.inputs[0]['device'], self.inputs[0]['host'], self.stream)
        self.context.set_tensor_address(self.inputs[0]['name'], int(self.inputs[0]['device']))
        self.context.set_tensor_address(self.outputs[0]['name'], int(self.outputs[0]['device']))
        self.context.execute_async_v3(stream_handle=self.stream.handle)
        cuda.memcpy_dtoh_async(self.outputs[0]['host'], self.outputs[0]['device'], self.stream)
        self.stream.synchronize()
        return self.outputs[0]['host']

    def detect(self, frame_rgb):
        original_height, original_width = frame_rgb.shape[:2]
        resized_frame = cv2.resize(frame_rgb, self.model_input_size, interpolation=cv2.INTER_LINEAR)

        # Fill pre-allocated buffer
        resized_frame = resized_frame.transpose(2, 0, 1).astype(np.float32) / 255.0
        np.copyto(self.input_buffer[0], resized_frame)

        output = self.infer(self.input_buffer)
        boxes = self._process_output(output)

        for box in boxes:
            box['bbox'][0] /= self.model_input_size[0]
            box['bbox'][1] /= self.model_input_size[1]
            box['bbox'][2] /= self.model_input_size[0]
            box['bbox'][3] /= self.model_input_size[1]

        return boxes

    def _process_output(self, output):
        CONFIDENCE_THRESHOLD = settings_manager.get("AI.confidence", 0.65)
        NMS_IOU_THRESHOLD = settings_manager.get("AI.nms_iou_threshold", 0.3)

        output = np.array(output).reshape((self.num_outputs, self.grid_cells))
        x_coords, y_coords, widths, heights, scores = output[:5]

        mask = scores > CONFIDENCE_THRESHOLD
        x_coords, y_coords, widths, heights, scores = x_coords[mask], y_coords[mask], widths[mask], heights[mask], scores[mask]

        if len(scores) == 0:
            return []

        boxes = np.column_stack([
            x_coords - widths / 2,
            y_coords - heights / 2,
            x_coords + widths / 2,
            y_coords + heights / 2
        ])

import numpy as np
import tensorrt as trt
import pycuda.autoinit
import pycuda.driver as cuda
import cv2
import torch
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
            # Set global visual settings
            global detectionOverlay, fpsOverlay, fovOverlay
            detectionOverlay = self.settings["Visual"]["target"]
            fpsOverlay = self.settings["Visual"]["fps"]
            fovOverlay = self.settings["Visual"]["fov"]
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


# Initialize settings manager at module level
settings_manager = SettingsManager()

class FastObjectDetector:
    def __init__(self, engine_path):
        self.stream = cuda.Stream()
        self.logger = trt.Logger(trt.Logger.WARNING)
        self.engine = self._load_engine(engine_path)
        self.context = self.engine.create_execution_context()
        self.inputs, self.outputs, self.bindings = self._allocate_buffers()
        self.model_input_size = (640, 640)
        self.input_buffer = np.empty((1, 3, *self.model_input_size), dtype=np.float32)  # Pre-allocated buffer

        # Output configuration
        output_tensor_name = self.engine.get_tensor_name(self.engine.num_io_tensors - 1)
        self.output_shape = self.engine.get_tensor_shape(output_tensor_name)
        if len(self.output_shape) == 3:
            self.num_classes = 1
            self.num_outputs = self.output_shape[1]
            self.grid_cells = self.output_shape[2]
        else:
            raise ValueError(f"Unexpected output shape: {self.output_shape}")

        self._warmup_engine()

    def _load_engine(self, engine_path):
        with open(engine_path, 'rb') as f:
            runtime = trt.Runtime(self.logger)
            return runtime.deserialize_cuda_engine(f.read())

    def _allocate_buffers(self):
        inputs, outputs, bindings = [], [], []
        for binding in self.engine:
            shape = self.engine.get_tensor_shape(binding)
            size = trt.volume(shape)
            dtype = trt.nptype(self.engine.get_tensor_dtype(binding))
            host_mem = cuda.pagelocked_empty(size, dtype)
            device_mem = cuda.mem_alloc(host_mem.nbytes)
            bindings.append(int(device_mem))
            if self.engine.get_tensor_mode(binding) == trt.TensorIOMode.INPUT:
                inputs.append({'host': host_mem, 'device': device_mem, 'name': binding})
            else:
                outputs.append({'host': host_mem, 'device': device_mem, 'name': binding})
        return inputs, outputs, bindings

    def _warmup_engine(self, num_warmup=10):
        dummy_input = np.zeros((1, 3, 640, 640), dtype=np.float32)
        for _ in range(num_warmup):
            self.infer(dummy_input)
        torch.cuda.synchronize()

    def infer(self, input_tensor):
        np.copyto(self.inputs[0]['host'], input_tensor.ravel())
        cuda.memcpy_htod_async(self.inputs[0]['device'], self.inputs[0]['host'], self.stream)
        self.context.set_tensor_address(self.inputs[0]['name'], int(self.inputs[0]['device']))
        self.context.set_tensor_address(self.outputs[0]['name'], int(self.outputs[0]['device']))
        self.context.execute_async_v3(stream_handle=self.stream.handle)
        cuda.memcpy_dtoh_async(self.outputs[0]['host'], self.outputs[0]['device'], self.stream)
        self.stream.synchronize()
        return self.outputs[0]['host']

    def detect(self, frame_rgb):
        original_height, original_width = frame_rgb.shape[:2]
        resized_frame = cv2.resize(frame_rgb, self.model_input_size, interpolation=cv2.INTER_LINEAR)

        # Fill pre-allocated buffer
        resized_frame = resized_frame.transpose(2, 0, 1).astype(np.float32) / 255.0
        np.copyto(self.input_buffer[0], resized_frame)

        output = self.infer(self.input_buffer)
        boxes = self._process_output(output)

        for box in boxes:
            box['bbox'][0] /= self.model_input_size[0]
            box['bbox'][1] /= self.model_input_size[1]
            box['bbox'][2] /= self.model_input_size[0]
            box['bbox'][3] /= self.model_input_size[1]

        return boxes

    def _process_output(self, output):
        CONFIDENCE_THRESHOLD = settings_manager.get("AI.confidence", 0.65)
        NMS_IOU_THRESHOLD = settings_manager.get("AI.nms_iou_threshold", 0.3)

        output = np.array(output).reshape((self.num_outputs, self.grid_cells))
        x_coords, y_coords, widths, heights, scores = output[:5]

        mask = scores > CONFIDENCE_THRESHOLD
        x_coords, y_coords, widths, heights, scores = x_coords[mask], y_coords[mask], widths[mask], heights[mask], scores[mask]

        if len(scores) == 0:
            return []

        boxes = np.column_stack([
            x_coords - widths / 2,
            y_coords - heights / 2,
            x_coords + widths / 2,
            y_coords + heights / 2
        ])

        indices = cv2.dnn.NMSBoxes(boxes.tolist(), scores.tolist(), CONFIDENCE_THRESHOLD, NMS_IOU_THRESHOLD).flatten()

        return [{'bbox': boxes[idx].tolist(),
                 'confidence': float(scores[idx]),
                 'class_name': 'object'} for idx in indices]

    def reload(self, engine_path):
        """Reloads the TensorRT engine from a new path."""
        try:
            print(f"Reloading model from {engine_path}...")
            # Clean up existing resources
            if hasattr(self, 'context'):
                del self.context
            if hasattr(self, 'engine'):
                del self.engine
            
            # Load new engine
            self.engine = self._load_engine(engine_path)
            self.context = self.engine.create_execution_context()
            
            # Re-allocate buffers
            # Note: We need to free old buffers first if we want to be perfectly clean, 
            # but Python's GC + CUDA driver usually handle this when the objects are lost.
            # However, for safety, let's just re-run allocation which creates new ones.
            self.inputs, self.outputs, self.bindings = self._allocate_buffers()
            
            # Update output configuration
            output_tensor_name = self.engine.get_tensor_name(self.engine.num_io_tensors - 1)
            self.output_shape = self.engine.get_tensor_shape(output_tensor_name)
            if len(self.output_shape) == 3:
                self.num_classes = 1
                self.num_outputs = self.output_shape[1]
                self.grid_cells = self.output_shape[2]
            else:
                raise ValueError(f"Unexpected output shape: {self.output_shape}")
            
            # Warmup
            self._warmup_engine()
            print("Model reload successful.")
            return True
        except Exception as e:
            print(f"Failed to reload model: {e}")
            return False

    def __del__(self):
        if hasattr(self, 'engine'):
            del self.engine
        if torch.cuda.is_available():
            torch.cuda.empty_cache()