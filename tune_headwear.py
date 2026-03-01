from ultralytics import YOLO
import os

def main():
    print("--- STEP 1: LOADING CONFIGURATION ---")
    dataset_yaml = os.path.abspath("headwear_dataset/data.yaml")

    if not os.path.exists(dataset_yaml):
        print(f"ERROR: Could not find {dataset_yaml}")
        return

    # --- TUNING FOR HEADWEAR (Small Object + Angles) ---
    tuned_hyperparameters = {
        'lr0': 0.01,
        'momentum': 0.937,
        'weight_decay': 0.0005,
        
        # --- AUGMENTATION ---
        # Rotation is GOOD here. People look down/up/sideways.
        'degrees': 15.0,         
        
        # Scale: Helmets can be close (at door) or far (in aisle).
        'scale': 0.5,            
        
        # Mosaic: Critical for small objects like caps/helmets.
        'mosaic': 1.0,           
        
        # Mixup: Helps separate "Helmet" from "Background Clutter"
        'mixup': 0.1,            
        
        # Color: Helmets come in all colors. Make the model color-agnostic.
        'hsv_h': 0.015,
        'hsv_s': 0.7,
        'hsv_v': 0.4,
        
        'fliplr': 0.5,           # Mirroring is safe
    }

    print("--- STEP 2: INITIALIZING HEADWEAR MODEL (MEDIUM) ---")
    # Using Medium model for better detail on small head accessories
    model = YOLO("yolov8n.pt") 

    print("--- STEP 3: STARTING TRAINING ---")
    results = model.train(
        data=dataset_yaml,
        epochs=50,               # 50 Epochs is sufficient for this task
        imgsz=640,
        batch=8,                 # Safe for RTX 3060
        device=0,
        project="Smart_Surveillance_FYP_Train", 
        name="headwear_tuned_v1", 
        patience=10,             # Early stopping
        **tuned_hyperparameters
    )

    print("--- SUCCESS ---")
    print(f"Model Saved at: Smart_Surveillance_FYP_Train/headwear_tuned_v1/weights/best.pt")

if __name__ == '__main__':
    main()