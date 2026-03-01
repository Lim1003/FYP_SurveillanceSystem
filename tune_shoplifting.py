from ultralytics import YOLO
import os

def main():
    print("--- STEP 1: LOADING CONFIGURATION ---")
    dataset_yaml = os.path.abspath("shoplifting_dataset/data.yaml")

    if not os.path.exists(dataset_yaml):
        print(f"ERROR: Could not find {dataset_yaml}")
        return

    # --- STRATEGY: ANTI-OVERFITTING TUNING ---
    # We are increasing difficulty so the model learns 'Concepts' not 'Backgrounds'
    tuned_hyperparameters = {
        'lr0': 0.01,             # Standard initial learning rate
        'lrf': 0.01,             # Final learning rate
        'momentum': 0.937,       # Standard momentum
        'weight_decay': 0.0005,  # Increased slightly to reduce memorization
        
        # --- LOSS GAINS ---
        'box': 7.5,              # High box gain = Be precise about location
        'cls': 0.5,              # Moderate class gain
        'dfl': 1.5,              # Distribution Focal Loss (helps with difficult angles)
        
        # --- AUGMENTATION (The Key to Action Recognition) ---
        'hsv_h': 0.015,          # Adjust hue (lighting changes)
        'hsv_s': 0.7,            # Adjust saturation (camera quality varies)
        'hsv_v': 0.4,            # Adjust brightness (shadows/glare)
        'degrees': 10.0,         # +/- 10 degrees rotation (simulates camera angles)
        'translate': 0.1,        # Shift image slightly
        'scale': 0.5,            # Zoom in/out (person distance varies)
        'shear': 2.5,            # Slight perspective shift
        'perspective': 0.0,      # Keep 0 for now (too much distortion can hurt)
        'flipud': 0.0,           # No upside down (people don't walk on ceilings)
        'fliplr': 0.5,           # Mirror left/right (essential for detection)
        
        # --- THE SECRET WEAPON ---
        'mosaic': 1.0,           # 4 images stitched together (Standard)
        'mixup': 0.15,           # Blend images! Forces model to find "ghost" objects.
                                 # This is the #1 fix for False Alarms.
        'copy_paste': 0.1,       # Copy objects to new backgrounds (Disconnects object from background)
    }

    print("--- STEP 2: INITIALIZING TUNED MODEL ---")
    # Load base model
    model = YOLO("yolov8n.pt") 

    print("--- STEP 3: STARTING ROBUST TRAINING ---")
    results = model.train(
        data=dataset_yaml,
        epochs=60,               # Increased to 75 (Harder training takes longer to learn)
        imgsz=640,
        batch=8,                 # Keep 8 for your 3060 Laptop
        device=0,                # Force RTX 3060
        project="Smart_Surveillance_FYP_Train", 
        name="shoplifting_tuned_v1", 
        patience=15,             # Wait longer before stopping (learning is harder now)
        **tuned_hyperparameters  # Inject the anti-overfitting rules
    )

    print("--- SUCCESS ---")
    print(f"Tuned Model Saved at: Smart_Surveillance_FYP_Train/shoplifting_tuned_v1/weights/best.pt")

if __name__ == '__main__':
    main()