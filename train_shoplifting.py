from ultralytics import YOLO
import os

def main():
    print("--- STEP 1: LOADING CONFIGURATION ---")
    # Absolute path to the dataset configuration
    dataset_yaml = os.path.abspath("shoplifting_dataset/data.yaml")

    # Verify file existence (Good practice from train_fall.py)
    if not os.path.exists(dataset_yaml):
        print(f"ERROR: Could not find {dataset_yaml}")
        print("Please check if you named the folder 'shoplifting_dataset' correctly.")
        return

    print("--- STEP 2: INITIALIZING BASIC TRAINING ---")
    # Load the base model (starting from scratch)
    model = YOLO("yolov8n.pt") 

    print("--- STEP 3: STARTING TRAINING (BASELINE) ---")
    # Training without custom hyperparameters.
    # We set epochs to 50 to allow the graph to show a performance plateau.
    results = model.train(
        data=dataset_yaml,
        epochs=50,               # Higher epochs to generate a useful graph
        imgsz=640,
        batch=8,                 # Safe batch size for RTX 3060 Laptop
        device=0,                # Force GPU
        project="Smart_Surveillance_FYP_Train", 
        name="shoplifting_model", # Name changed to indicate this is a baseline test
        patience=10              # [Optional] Stop if no improvement for 10 epochs
    )

    print("--- SUCCESS ---")
    print(f"Training Complete. Check 'Smart_Surveillance_FYP_Train/shoplifting_model' for graphs.")

if __name__ == '__main__':
    main()