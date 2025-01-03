import numpy as np
import tensorrt as trt
import pycuda.autoinit
import pycuda.driver as cuda
import cv2
import torch


class FastObjectDetector:
    def __init__(self, engine_path):
        self.stream = cuda.Stream()
        self.logger = trt.Logger(trt.Logger.WARNING)
        self.engine = self._load_engine(engine_path)
        self.context = self.engine.create_execution_context()
        self.inputs, self.outputs, self.bindings = self._allocate_buffers()

        # Model expects 640x640 input
        self.model_input_size = (640, 640)

        # Get output dimensions from the engine
        output_tensor_name = self.engine.get_tensor_name(self.engine.num_io_tensors - 1)
        self.output_shape = self.engine.get_tensor_shape(output_tensor_name)
        print(f"Model output shape: {self.output_shape}")

        # Calculate grid size based on output shape
        if len(self.output_shape) == 3:  # Batch, Elements, Grid cells
            self.num_classes = 1  # YOLOv8 detection model
            self.num_outputs = self.output_shape[1]
            self.grid_cells = self.output_shape[2]
        else:
            raise ValueError(f"Unexpected output shape: {self.output_shape}")

        print(f"Grid cells: {self.grid_cells}, Outputs: {self.num_outputs}")
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
        # Get original dimensions
        original_height, original_width = frame_rgb.shape[:2]

        # Resize the frame to model input size
        resized_frame = cv2.resize(frame_rgb, self.model_input_size, interpolation=cv2.INTER_LINEAR)

        # Prepare input tensor
        input_tensor = resized_frame.transpose(2, 0, 1).astype(np.float32) / 255.0
        input_tensor = np.ascontiguousarray(input_tensor[np.newaxis, ...])

        # Run inference
        output = self.infer(input_tensor)

        # Process output and normalize coordinates
        boxes = self._process_output(output)

        # Convert coordinates to be relative to original frame size
        for box in boxes:
            # Normalize coordinates to 0-1 range
            box['bbox'][0] /= self.model_input_size[0]  # x1
            box['bbox'][1] /= self.model_input_size[1]  # y1
            box['bbox'][2] /= self.model_input_size[0]  # x2
            box['bbox'][3] /= self.model_input_size[1]  # y2

        return boxes

    def _process_output(self, output):
        CONFIDENCE_THRESHOLD = 0.7
        NMS_IOU_THRESHOLD = 0.01

        # Reshape based on the model's output shape
        output = np.array(output).reshape((self.num_outputs, self.grid_cells))

        # Extract coordinates and scores
        x_coords, y_coords, widths, heights, scores = output[:5]  # Take first 5 rows

        mask = scores > CONFIDENCE_THRESHOLD
        x_coords, y_coords, widths, heights, scores = x_coords[mask], y_coords[mask], widths[mask], heights[mask], \
        scores[mask]

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

    def __del__(self):
        if hasattr(self, 'engine'):
            del self.engine
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

# TensorRTInference class remains the same as in your original code
class TensorRTInference:
    def __init__(self, engine_path):
        self.stream = cuda.Stream()
        self.logger = trt.Logger(trt.Logger.WARNING)

        # Load engine
        with open(engine_path, 'rb') as f:
            runtime = trt.Runtime(self.logger)
            self.engine = runtime.deserialize_cuda_engine(f.read())

        if not self.engine:
            raise RuntimeError('Failed to load engine')

        self.context = self.engine.create_execution_context()

        # Get profile info
        print(f"Number of optimization profiles: {self.engine.num_optimization_profiles}")

        # Get tensor names
        print("\nTensor Information:")
        num_io_tensors = self.engine.num_io_tensors
        print(f"Number of I/O tensors: {num_io_tensors}")

        self.input_tensors = []
        self.output_tensors = []
        self.input_bindings = []
        self.output_bindings = []

        for i in range(num_io_tensors):
            name = self.engine.get_tensor_name(i)
            mode = self.engine.get_tensor_mode(name)  # Now using name instead of index
            shape = self.engine.get_tensor_shape(name)
            dtype = self.engine.get_tensor_dtype(name)

            print(f"Tensor {i}:")
            print(f"  Name: {name}")
            print(f"  Mode: {mode}")
            print(f"  Shape: {shape}")
            print(f"  Dtype: {dtype}")

            # Allocate memory
            size = trt.volume(shape)
            host_mem = cuda.pagelocked_empty(size, trt.nptype(dtype))
            device_mem = cuda.mem_alloc(host_mem.nbytes)

            if mode == trt.TensorIOMode.INPUT:
                self.input_tensors.append({
                    'name': name,
                    'shape': shape,
                    'dtype': dtype,
                    'host': host_mem,
                    'device': device_mem
                })
                self.input_bindings.append(int(device_mem))
            else:
                self.output_tensors.append({
                    'name': name,
                    'shape': shape,
                    'dtype': dtype,
                    'host': host_mem,
                    'device': device_mem
                })
                self.output_bindings.append(int(device_mem))

        self.bindings = self.input_bindings + self.output_bindings

        if not self.input_tensors:
            raise RuntimeError("No input tensors found in engine")
        if not self.output_tensors:
            raise RuntimeError("No output tensors found in engine")

    def infer(self, input_tensor):
        if not self.input_tensors:
            raise RuntimeError("No input tensors available")

        # Verify input shape matches expected shape
        expected_size = trt.volume(self.input_tensors[0]['shape'])
        if input_tensor.size != expected_size:
            raise ValueError(f"Input tensor size mismatch. Expected {expected_size}, got {input_tensor.size}")

        # Copy input data to GPU
        np.copyto(self.input_tensors[0]['host'], input_tensor.ravel())
        cuda.memcpy_htod(self.input_tensors[0]['device'], self.input_tensors[0]['host'])

        # Execute inference
        if not self.context.execute_v2(bindings=self.bindings):
            raise RuntimeError("Inference failed")

        # Copy outputs back to CPU
        results = []
        for out in self.output_tensors:
            cuda.memcpy_dtoh(out['host'], out['device'])
            results.append(out['host'])

        return results

    def __del__(self):
        try:
            for tensor in self.input_tensors + self.output_tensors:
                tensor['device'].free()
        except:
            pass