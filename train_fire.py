from ultralytics import YOLO
import os

def main():
    print("--- STEP 1: LOADING LOCAL FIRE DATASET ---")
    
    # Point to the data.yaml in your new folder
    dataset_yaml = os.path.abspath("fire_dataset/data.yaml")

    print(f"Targeting dataset at: {dataset_yaml}")

    if not os.path.exists(dataset_yaml):
        print(f"ERROR: Could not find {dataset_yaml}")
        print("Please check if you named the folder 'fire_dataset' correctly.")
        return

    print("--- STEP 2: STARTING FIRE TRAINING ON RTX 3060 ---")
    
    # Load base model
    model = YOLO("yolov8n.pt") 

    # Train
    results = model.train(
        data=dataset_yaml,
        epochs=60,           
        imgsz=640,
        batch=8,
        device=0,            
        project="Smart_Surveillance_FYP_Train", 
        name="fire_model"    # Saving as 'fire_model'
    )

    print("--- TRAINING FINISHED ---")
    print("New model saved at: Smart_Surveillance_FYP_Train/fire_model/weights/best.pt")

if __name__ == '__main__':
    main()