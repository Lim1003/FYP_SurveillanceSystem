from ultralytics import YOLO
import os

def main():
    print("--- STEP 1: LOADING CONFIGURATION ---")
    dataset_yaml = os.path.abspath("shoplifting_dataset/data.yaml")
    
    # These are the winning values from your tuning session (Iteration 4)
    tuned_hyperparameters = {
        'lr0': 0.00997,          # Initial Learning Rate
        'lrf': 0.01007,          # Final Learning Rate cycle
        'momentum': 0.91838,     # Momentum (SGD)
        'weight_decay': 0.00049, # Regularization to prevent overfitting
        'box': 7.79637,          # Box Loss Gain (Higher = stricter bounding boxes)
        'cls': 0.55256,          # Classification Loss Gain
        'iou': 0.71002,          # IoU threshold for training
        'mosaic': 1.0,           # Mosaic augmentation active
        'mixup': 0.0,            # Mixup turned off (as per tuning result)
        'degrees': 0.0,          # Rotation turned off
    }

    print("--- STEP 2: INITIALIZING FINAL TRAINING ---")
    # Load the base model again to start fresh
    model = YOLO("yolov8n.pt") 

    print("--- STEP 3: TRAINING WITH OPTIMIZED PARAMETERS ---")
    # We pass **tuned_hyperparameters to unpack them into the train function
    results = model.train(
        data=dataset_yaml,
        epochs=30,              # Increased from 30 to 100 for final convergence
        imgsz=640,
        batch=8,
        device=0,                # RTX 3060
        project="Smart_Surveillance_FYP_Train",
        name="shoplifting_optimized_model",
        **tuned_hyperparameters  # <--- This injects your tuned metrics!
    )

    print("--- SUCCESS ---")
    print(f"Final Model Saved at: Smart_Surveillance_FYP_Train/shoplifting_model/weights/best.pt")

if __name__ == '__main__':
    main()