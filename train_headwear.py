from ultralytics import YOLO
import os

def main():
    print("--- STEP 1: LOADING LOCAL HEADWEAR DATASET ---")
    dataset_yaml = os.path.abspath("headwear_dataset/data.yaml")

    if not os.path.exists(dataset_yaml):
        print(f"ERROR: Could not find {dataset_yaml}")
        return

    print("--- STEP 2: STARTING HEADWEAR TRAINING ON RTX 3060 ---")
    model = YOLO("yolov8n.pt") 

    results = model.train(
        data=dataset_yaml,
        epochs=20,           
        imgsz=640,
        batch=8,
        device=0,            
        project="Smart_Surveillance_FYP_Train", 
        name="headwear_model"    
    )
    print("--- TRAINING FINISHED ---")

if __name__ == '__main__':
    main()