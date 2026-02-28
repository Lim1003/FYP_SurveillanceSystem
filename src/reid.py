import torch
import torch.nn as nn
from torchvision import transforms
from scipy.spatial.distance import cosine
import numpy as np
import sys
import os

# --- THIS PART IS VITAL FOR MANUAL INSTALL ---
current_dir = os.path.dirname(os.path.abspath(__file__))
local_repo_path = os.path.join(current_dir, 'deep_person_reid')

# Adds your manual folder to Python's "Search Path"
if local_repo_path not in sys.path:
    sys.path.append(local_repo_path)

try:
    import torchreid
except ImportError as e:
    print(f"Error: Could not find 'torchreid'. Make sure the folder 'src/deep_person_reid' exists.")
    raise e
# ---------------------------------------------

class PersonReID:
    def __init__(self, distance_threshold=0.4): 
        print("[ReID] Initializing Omni-Scale Network (OSNet)...")
        
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.distance_threshold = distance_threshold 
        
        # Build Model using the local library
        self.model = torchreid.models.build_model(
            name='osnet_x1_0',
            num_classes=1000,
            loss='softmax',
            pretrained=True
        )
            
        self.model.to(self.device)
        self.model.eval() 
        
        self.preprocess = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((256, 128)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        
        self.known_people = {} 
        self.next_global_id = 1

    def extract_features(self, img_crop):
        if img_crop.size == 0: return None
        img_tensor = self.preprocess(img_crop).unsqueeze(0).to(self.device)
        with torch.no_grad():
            features = self.model(img_tensor)
        return features.cpu().numpy().flatten()

    # [UPDATED] resolve_id now accepts 'used_ids' to prevent duplicates
    def resolve_id(self, yolo_id, frame, box, used_ids=set()):
        h, w, _ = frame.shape
        x1, y1, x2, y2 = map(int, box)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        person_crop = frame[y1:y2, x1:x2]
        if person_crop.size == 0: return yolo_id

        current_features = self.extract_features(person_crop)
        if current_features is None: return yolo_id

        best_match_id = None
        min_dist = 1.0 

        for pid, data in self.known_people.items():
            # Skip IDs that are already assigned in this frame
            if pid in used_ids:
                continue

            dist = cosine(data['features'], current_features)
            
            # [TWEAK] Stricter threshold (0.35) to reduce false matches
            if dist < 0.35 and dist < min_dist:
                min_dist = dist
                best_match_id = pid
        
        if best_match_id:
            alpha = 0.15
            self.known_people[best_match_id]['features'] = (1-alpha)*self.known_people[best_match_id]['features'] + alpha*current_features
            return best_match_id
        else:
            new_id = self.next_global_id
            self.known_people[new_id] = {'features': current_features}
            self.next_global_id += 1
            return new_id