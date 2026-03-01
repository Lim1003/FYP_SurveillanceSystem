from ultralytics import YOLO
import os

def main():
    print("--- STEP 1: LOADING CONFIGURATION ---")
    
    # Absolute path to the data.yaml file
    # Ensure this file contains "nc: 2" and "names: ['fire', 'smoke']"
    dataset_yaml = os.path.abspath("fire_dataset/data.yaml")

    # Verify the file exists before starting
    if not os.path.exists(dataset_yaml):
        print(f"[ERROR] Could not find {dataset_yaml}")
        print("Please check if the folder 'fire_dataset' exists and contains data.yaml")
        return

    print(f"Targeting dataset: {dataset_yaml}")
    print("--- STEP 2: INITIALIZING FIRE & SMOKE TRAINING ---")
    
    # Load the base model (Pre-trained on COCO)
    # YOLO will automatically replace the last layer to match your 2 classes
    model = YOLO("yolov8n.pt") 

    print("--- STEP 3: STARTING TRAINING ---")
    results = model.train(
        data=dataset_yaml,
        epochs=50,
        imgsz=640,
        batch=8,             # Optimized for RTX 3060 Laptop
        device=0,            # Use GPU
        project="Smart_Surveillance_FYP_Train", 
        name="fire_model",   # This will create 'Smart_Surveillance_FYP_Train/fire_model'
        patience=10          # [NEW] Stop if no improvement for 10 epochs (Saves time)
    )

    print("--- SUCCESS ---")
    print(f"Final Model Saved at: Smart_Surveillance_FYP_Train/fire_model/weights/best.pt")

if __name__ == '__main__':
    main()