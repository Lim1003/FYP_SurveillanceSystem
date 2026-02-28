from ultralytics import YOLO
import os

def main():
    print("--- STARTING PERFORMANCE EVALUATION: SHOPLIFTING ---")
    
    # 1. Load your optimized Shoplifting Model
    # Make sure this path points to your BEST weights
    model_path = 'Smart_Surveillance_FYP_Train/shoplifting_model/weights/best.pt'
    model = YOLO(model_path)

    # 2. Run Validation
    # This compares predictions vs. labels in your 'dataset/data.yaml' (val images)
    # plots=True will generate the Confusion Matrix and PR-Curve
    metrics = model.val(
        data='shoplifting_dataset/data.yaml', 
        split='val',              # Use validation set
        project='Model_Metrics',
        name='shoplifting_eval',
        plots=True                # Generate visual graphs
    )

    print("\n" + "="*40)
    print("      FINAL PERFORMANCE METRICS      ")
    print("="*40)

    # 3. Extract and Print Key Metrics
    
    # A. mAP (Mean Average Precision)
    # This is the "Gold Standard" accuracy score.
    # mAP50 = Accuracy when we accept any overlap > 50%
    print(f"1. mAP@50 (Standard Accuracy): {metrics.box.map50:.4f}")
    
    # mAP50-95 = Strict Accuracy (Average of 50% to 95% overlap)
    print(f"   mAP@50-95 (Strict Accuracy): {metrics.box.map:.4f}")

    # B. AP (Average Precision) per Class
    # Since you might have multiple classes in the dataset (e.g., 'shoplifting', 'person'), 
    # we print them individually.
    print("\n2. AP (Average Precision) per Class:")
    # metrics.names maps ID to Name (e.g., {0: 'theft'})
    # metrics.box.maps is an array of AP scores for each class
    for i, ap_score in enumerate(metrics.box.maps):
        class_name = metrics.names[i]
        print(f"   - Class '{class_name}': {ap_score:.4f}")

    # C. Precision & Recall (Components of AP)
    print(f"\n3. Global Precision: {metrics.box.mp:.4f} (How trustworthy is a 'Theft' alert?)")
    print(f"   Global Recall:    {metrics.box.mr:.4f} (How many thefts did we catch?)")

    print("\n" + "="*40)
    print("Graphs saved at: Model_Metrics/shoplifting_eval/")

if __name__ == '__main__':
    main()