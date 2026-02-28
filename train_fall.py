from ultralytics import YOLO
import os

def main():
    print("--- STEP 1: LOADING LOCAL FALL DATASET ---")
    
    # 1. Point to the data.yaml in your new folder
    # We use abspath to ensure Windows finds the file correctly
    dataset_yaml = os.path.abspath("fall_dataset/data.yaml")

    print(f"Targeting dataset at: {dataset_yaml}")

    # Check if file actually exists to prevent errors
    if not os.path.exists(dataset_yaml):
        print(f"ERROR: Could not find {dataset_yaml}")
        print("Please check if you named the folder 'fall_dataset' correctly.")
        return

    print("--- STEP 2: STARTING FALL TRAINING ON RTX 3060 ---")
    
    # Load the base model (starting from scratch with a smart brain)
    model = YOLO("yolov8n.pt") 

    # Train the model
    results = model.train(
        data=dataset_yaml,   # Pointing to local file
        epochs=20,           # 20 Epochs is good for a demo
        imgsz=640,
        batch=8,             # Safe batch size for RTX 3060 Laptop
        device=0,            # Force GPU
        project="Smart_Surveillance_FYP_Train", # Save in the same main folder
        name="fall_model"    # Name the specific sub-folder 'fall_model'
    )

    print("--- TRAINING FINISHED ---")
    print("New model saved at: Smart_Surveillance_FYP_Train/fall_model/weights/best.pt")

if __name__ == '__main__':
    main()