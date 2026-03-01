from ultralytics import YOLO
import os

def main():
    print("--- STEP 1: LOADING CONFIGURATION ---")
    dataset_yaml = os.path.abspath("fall_dataset/data.yaml")

    if not os.path.exists(dataset_yaml):
        print(f"ERROR: Could not find {dataset_yaml}")
        return

    # --- TUNING SPECIFICALLY FOR FALL DETECTION ---
    tuned_hyperparameters = {
        'lr0': 0.01,
        'lrf': 0.01,
        'momentum': 0.937,
        'weight_decay': 0.0005,
        
        # --- ORIENTATION RULES (CRITICAL) ---
        # We keep rotation LOW. If we rotate a standing person 90 degrees, 
        # the model learns "Horizontal = Standing", which ruins fall detection.
        'degrees': 0.0,          # Keep 0.0 to preserve "Vertical vs Horizontal" logic
        
        # --- GEOMETRY & SIZE ---
        'scale': 0.6,            # High scaling: Learns falls close up AND far away
        'shear': 0.0,            # Keep 0 to prevent distorting body shapes
        'translate': 0.1,        # Shift position slightly
        'flipud': 0.0,           # No upside-down augmentation
        'fliplr': 0.5,           # Mirror Left/Right is safe and good
        
        # --- FALSE ALARM REDUCTION ---
        # 1. MOSAIC: Forces model to find people in complex scenes (clutter)
        'mosaic': 1.0,           
        
        # 2. MIXUP: Blends images. Helps distinguish "Person lying on sofa" (Background) 
        #    from "Person falling on floor" (Action).
        'mixup': 0.15,           
        
        # 3. BOX GAIN: Stricter penalty for sloppy boxes.
        'box': 7.5,              
        
        # 4. CLASS GAIN: Focus on distinguishing 'Fall' vs 'Stand' vs 'Head'
        'cls': 0.5,              
    }

    print("--- STEP 2: INITIALIZING TUNED MODEL (MEDIUM) ---")
    # Using Medium model as requested for better intelligence
    model = YOLO("yolov8n.pt") 

    print("--- STEP 3: STARTING ROBUST TRAINING ---")
    results = model.train(
        data=dataset_yaml,
        epochs=60,               # Medium model needs more time to converge
        imgsz=640,
        batch=8,                 # Safe for RTX 3060
        device=0,
        project="Smart_Surveillance_FYP_Train", 
        name="fall_tuned_v1", 
        patience=10,             # Stop early if accuracy plateaus
        **tuned_hyperparameters  # Apply the Anti-False-Alarm rules
    )

    print("--- SUCCESS ---")
    print(f"Tuned Model Saved at: Smart_Surveillance_FYP_Train/fall_tuned_v1/weights/best.pt")

if __name__ == '__main__':
    main()