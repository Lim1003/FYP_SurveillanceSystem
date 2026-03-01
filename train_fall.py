from ultralytics import YOLO
import os

def main():
    print("--- STEP 1: LOADING LOCAL FALL DATASET ---")
    
    # Absolute path to the dataset configuration
    # Ensure your data.yaml is inside the 'fall_dataset' folder
    dataset_yaml = os.path.abspath("fall_dataset/data.yaml")

    print(f"Targeting dataset at: {dataset_yaml}")

    if not os.path.exists(dataset_yaml):
        print(f"[ERROR] Could not find {dataset_yaml}")
        print("Please check if you named the folder 'fall_dataset' correctly.")
        return

    print("--- STEP 2: STARTING FALL TRAINING (MEDIUM MODEL) ---")
    
    model = YOLO("yolov8n.pt") 

    print("--- STEP 3: STARTING TRAINING ---")
    results = model.train(
        data=dataset_yaml,
        epochs=60,           # Increased to 60 to allow convergence
        imgsz=640,
        batch=8,             # RTX 3060 can handle Batch 8 for Medium
        device=0,            # Force GPU
        project="Smart_Surveillance_FYP_Train", 
        name="fall_model", # specific name to distinguish from previous runs
        patience=10          # Stop if no improvement for 10 epochs
    )

    print("--- SUCCESS ---")
    print(f"Final Model Saved at: Smart_Surveillance_FYP_Train/fall_model/weights/best.pt")

if __name__ == '__main__':
    main()