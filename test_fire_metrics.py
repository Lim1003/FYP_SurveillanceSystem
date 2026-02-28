from ultralytics import YOLO
import os

def main():
    print("--- STARTING PERFORMANCE EVALUATION: FIRE & SMOKE ---")
    
    # 1. Load your Fire Model
    # Ensure this matches the folder name where your best fire training result is
    # (Check if it is 'fire_model', 'fire_model2', or 'fire_model_augmented')
    model_path = 'Smart_Surveillance_FYP_Train/fire_model/weights/best.pt'
    
    if not os.path.exists(model_path):
        print(f"ERROR: Model not found at {model_path}")
        return

    model = YOLO(model_path)

    # 2. Run Validation
    # Important: Ensure 'fire_dataset/data.yaml' has ABSOLUTE PATHS inside it
    # just like you did for the shoplifting dataset.
    metrics = model.val(
        data='fire_dataset/data.yaml', 
        split='val',              
        project='Model_Metrics',
        name='fire_eval',
        plots=True                
    )

    print("\n" + "="*40)
    print("      FINAL PERFORMANCE METRICS      ")
    print("="*40)

    # 3. Extract Key Metrics
    print(f"1. mAP@50 (Standard Accuracy): {metrics.box.map50:.4f}")
    print(f"   mAP@50-95 (Strict Accuracy): {metrics.box.map:.4f}")

    # 4. Breakdown by Class (Fire vs Smoke vs Others)
    print("\n2. AP (Average Precision) per Class:")
    
    # This loop automatically handles however many classes you have (3 in this case)
    # It maps the Class ID (0, 1, 2) to the Name ('fire', 'others', 'smoke')
    for i, ap_score in enumerate(metrics.box.maps):
        # Safety check to avoid index errors if class names aren't fully populated
        if i in metrics.names:
            class_name = metrics.names[i]
            print(f"   - Class '{class_name}': {ap_score:.4f}")

    print(f"\n3. Global Precision: {metrics.box.mp:.4f}")
    print(f"   Global Recall:    {metrics.box.mr:.4f}")

    print("\n" + "="*40)
    print("Graphs saved at: Model_Metrics/fire_eval/")

if __name__ == '__main__':
    main()