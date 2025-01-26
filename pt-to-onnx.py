from ultralytics import YOLO

# Load the YOLOv8 model
model = YOLO('csgo2_best.pt')

# Export the model to ONNX format
model.export(format='onnx')