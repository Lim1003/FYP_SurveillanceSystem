from ultralytics import YOLO
import os

def main():
    print("--- STEP 1: LOADING CONFIGURATION ---")
    dataset_yaml = os.path.abspath("fire_dataset/data.yaml")

    if not os.path.exists(dataset_yaml):
        print(f"ERROR: Could not find {dataset_yaml}")
        return

    # --- TUNING FOR SMALL / DISTANT FIRE ---
    tuned_hyperparameters = {
        'lr0': 0.01,
        'lrf': 0.01,
        'momentum': 0.937,
        'weight_decay': 0.0005,
        
        # --- AUGMENTATION (The Fix for Distance) ---
        # 1. MOSAIC: Stitches 4 images. Makes objects smaller. Crucial for "Far Fire".
        'mosaic': 1.0,           
        
        # 2. SCALE: High value (0.8) means we randomly shrink images by up to 80%.
        #    This simulates "Fire far away" mathematically.
        'scale': 0.8,            
        
        # 3. MIXUP: Blends images. Helps prevent confusing "Red Shirt" with "Fire".
        'mixup': 0.1,
        
        # 4. COLOR: Fire color changes based on camera quality/lighting.
        'hsv_h': 0.015,          # Hue variance
        'hsv_s': 0.7,            # Saturation variance (Bright vs Dull fire)
        'hsv_v': 0.4,            # Brightness variance (Night vs Day fire)
        
        # 5. OTHER
        'degrees': 0.0,          # Fire usually goes up, no rotation needed.
        'translate': 0.1,
        'shear': 0.0,
        'flipud': 0.0,
        'fliplr': 0.5,           # Mirroring is fine
        
        # 6. COPY-PASTE: Pastes fire onto random backgrounds. 
        #    Helps the model learn "Fire" is an object, not a background.
        'copy_paste': 0.3        
    }

    print("--- STEP 2: INITIALIZING TUNED FIRE MODEL ---")
    model = YOLO("yolov8n.pt") 

    print("--- STEP 3: STARTING ROBUST TRAINING ---")
    results = model.train(
        data=dataset_yaml,
        epochs=80,               # Harder tasks need more time (Increased to 80)
        imgsz=640,
        batch=8,                 # Safe for RTX 3060
        device=0,
        project="Smart_Surveillance_FYP_Train", 
        name="fire_tuned_v1", 
        patience=15,             # Wait longer for improvement
        **tuned_hyperparameters  # Apply the Small Object logic
    )

    print("--- SUCCESS ---")
    print(f"Final Model Saved at: Smart_Surveillance_FYP_Train/fire_tuned_v1/weights/best.pt")

if __name__ == '__main__':
    main()