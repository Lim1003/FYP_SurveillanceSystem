# import cv2
# import numpy as np
# import time
# import os
# import winsound
# from datetime import datetime
# from ultralytics import YOLO
# from ultralytics.utils.plotting import Annotator, colors
# from src.liveness import LivenessDetector

# # ==========================================
# #        CONFIGURATION & SETTINGS
# # ==========================================

# # SOURCE = 'test_data/fire0.mp4'
# SOURCE = 'test_data/fall1.mp4'
# # SOURCE = 'test_data/shoplift2.mp4'

# # SOURCE = 0
# # POSE_PATH     = 'checkpoints/yolov8n-pose.pt'
# POSE_PATH = 'yolov8m-pose.pt'
# SHOPLIFT_PATH = 'Smart_Surveillance_FYP_Train/shoplifting_model/weights/best.pt'
# FALL_PATH     = 'Smart_Surveillance_FYP_Train/fall_model/weights/best.pt'
# FIRE_PATH     = 'Smart_Surveillance_FYP_Train/fire_model/weights/best.pt'
# FACE_PATH     = 'Smart_Surveillance_FYP_Train/face_model/weights/best.pt'
# HEADWEAR_PATH = 'Smart_Surveillance_FYP_Train/headwear_model/weights/best.pt'

# # Sensitivity Thresholds
# CONF_FIRE      = 0.60
# CONF_SMOKE     = 0.60 # New threshold for smoke
# CONF_FALL      = 0.60
# CONF_THEFT     = 0.80
# CONF_FACE      = 0.60
# CONF_HEADWEAR  = 0.70
# ANGLE_THRESH   = 50

# # Snapshot Settings
# SNAPSHOT_DIR = "evidence_snapshots"
# COOLDOWN_SEC = 2.0         # Cooldown for snapshots
# SOUND_COOLDOWN = 2.0       # Don't play sound more often than every 3 seconds

# # ==========================================
# #           SOUND MANAGER CLASS
# # ==========================================
# class SoundAlertSystem:
#     def __init__(self):
#         self.last_alert_time = 0
        
#     def trigger(self, status):
#         """
#         Plays a specific windows system sound based on urgency.
#         FLAGS: 
#           SND_ASYNC = Play in background (Don't freeze video)
#           SND_ALIAS = Use Windows system event sounds
#         """
#         current_time = time.time()
        
#         # Check Cooldown (prevent sound spamming)
#         if current_time - self.last_alert_time < SOUND_COOLDOWN:
#             return

#         if status == "FIRE":
#             # "SystemHand" is usually the Critical Stop 'BONG' sound
#             winsound.PlaySound("SystemHand", winsound.SND_ALIAS | winsound.SND_ASYNC)
#             self.last_alert_time = current_time
            
#         elif status == "FALL":
#             # "SystemExclamation" is the Warning 'Ding'
#             winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)
#             self.last_alert_time = current_time
            
#         elif status == "THEFT":
#             # "SystemAsterisk" is the Info 'Dung' (Subtle)
#             winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
#             self.last_alert_time = current_time

# # Initialize Sound System
# sound_system = SoundAlertSystem()

# # ==========================================
# #       CUSTOM VISUALIZATION FUNCTIONS
# # ==========================================

# def draw_corner_rect(img, pt1, pt2, color, corner_thickness=5, connect_thickness=1):
#     """
#     Draws an "advanced" style framing box with thick corners and thin connectors.
#     """
#     x1, y1 = pt1
#     x2, y2 = pt2
    
#     # 1. Draw thin connecting lines (the base rectangle)
#     cv2.rectangle(img, pt1, pt2, color, connect_thickness)

#     # 2. Calculate corner length dynamically based on box size (e.g., 20% of shortest side)
#     # Ensure it's at least 20 pixels long so it's visible
#     length = min(abs(x2-x1), abs(y2-y1)) * 0.2
#     l = int(max(length, 20)) 

#     # 3. Draw thick corner brackets
#     # Top-Left
#     cv2.line(img, (x1, y1), (x1 + l, y1), color, corner_thickness)
#     cv2.line(img, (x1, y1), (x1, y1 + l), color, corner_thickness)
#     # Top-Right
#     cv2.line(img, (x2, y1), (x2 - l, y1), color, corner_thickness)
#     cv2.line(img, (x2, y1), (x2, y1 + l), color, corner_thickness)
#     # Bottom-Left
#     cv2.line(img, (x1, y2), (x1 + l, y2), color, corner_thickness)
#     cv2.line(img, (x1, y2), (x1, y2 - l), color, corner_thickness)
#     # Bottom-Right
#     cv2.line(img, (x2, y2), (x2 - l, y2), color, corner_thickness)
#     cv2.line(img, (x2, y2), (x2, y2 - l), color, corner_thickness)

# def draw_text_inside(img, text, x1, y1, color):
#     # Padding to move text inside the box
#     pad_x, pad_y = 10, 25
#     font_scale = 0.6
    
#     # Draw black outline (thickness 3)
#     cv2.putText(img, text, (x1 + pad_x, y1 + pad_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0,0,0), 3)
#     # Draw colored text (thickness 2)
#     cv2.putText(img, text, (x1 + pad_x, y1 + pad_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2)

# # ==========================================
# #           HELPER FUNCTIONS
# # ==========================================

# if not os.path.exists(SNAPSHOT_DIR): os.makedirs(SNAPSHOT_DIR)
# last_snapshot_times = {}

# def calculate_iou(box1, box2):
#     x1 = max(box1[0], box2[0])
#     y1 = max(box1[1], box2[1])
#     x2 = min(box1[2], box2[2])
#     y2 = min(box1[3], box2[3])
#     intersection_area = max(0, x2 - x1) * max(0, y2 - y1)
#     box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
#     if box1_area == 0: return 0
#     return intersection_area / box1_area

# def draw_hud(frame, fps, status, label, angle):
#     """
#     Draws the Top-Left status text with dynamic scaling based on frame resolution.
#     """
#     # 1. Get current frame dimensions
#     height, width = frame.shape[:2]
    
#     # 2. Calculate Scaling Factor
#     # We use 720p (height=720) as the "baseline" where scale = 1.0
#     # If video is 4K (2160p), scale becomes 3.0. If 360p, scale becomes 0.5.
#     scale = height / 720.0
    
#     # 3. Dynamic Font Configuration
#     # We enforce a minimum scale of 0.5 so text is never unreadable on tiny videos
#     font_scale_main = max(0.5, 0.7 * scale)
#     font_scale_sub  = max(0.4, 0.5 * scale)
    
#     # Dynamic Thickness (thicker line for bigger video)
#     thick_main = max(2, int(2 * scale))
#     thick_sub  = max(1, int(1 * scale))
    
#     # Dynamic Positioning (move text down further on big videos)
#     margin_x = int(10 * scale)
#     pos_y1   = int(30 * scale) # Top line
#     pos_y2   = int(60 * scale) # Bottom line

#     # 4. Define Colors & Text
#     if status == "FIRE":       color, text = (0, 0, 255), f"EMERGENCY: {label}"
#     elif status == "FALL":     color, text = (255, 0, 255), f"MEDICAL: {label}"
#     elif status == "THEFT":    color, text = (0, 165, 255), f"SECURITY: {label}"
#     elif status == "CONCEALED":color, text = (0, 255, 255), f"CAUTION: {label}"
#     else:                      color, text = (0, 255, 0), "SYSTEM NORMAL"

#     # 5. Draw Main Status (Text + Black Outline)
#     # Outline (Thickness + 2)
#     cv2.putText(frame, text, (margin_x, pos_y1), cv2.FONT_HERSHEY_SIMPLEX, 
#                 font_scale_main, (0,0,0), thick_main + 2)
#     # Color Text
#     cv2.putText(frame, text, (margin_x, pos_y1), cv2.FONT_HERSHEY_SIMPLEX, 
#                 font_scale_main, color, thick_main)
    
#     # 6. Draw Stats Sub-line
#     stats = f"FPS: {fps:.1f} | Angle: {int(angle)}deg"
    
#     cv2.putText(frame, stats, (margin_x, pos_y2), cv2.FONT_HERSHEY_SIMPLEX, 
#                 font_scale_sub, (0,0,0), thick_sub + 2)
#     cv2.putText(frame, stats, (margin_x, pos_y2), cv2.FONT_HERSHEY_SIMPLEX, 
#                 font_scale_sub, (255,255,255), thick_sub)

# def save_evidence(frame, status, label):
#     global last_snapshot_times
#     current_time = time.time()
#     if status in last_snapshot_times:
#         if current_time - last_snapshot_times[status] < COOLDOWN_SEC: return
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     filename = f"{SNAPSHOT_DIR}/{status}_{timestamp}.jpg"
#     cv2.imwrite(filename, frame)
#     print(f"📸 EVIDENCE CAPTURED: {filename}")
#     last_snapshot_times[status] = current_time

# # ==========================================
# #           MAIN APPLICATION
# # ==========================================

# def main():
#     print("--- INITIALIZING TARGETED ID SYSTEM ---")
#     model_pose = YOLO(POSE_PATH)
#     model_shoplift = YOLO(SHOPLIFT_PATH)
#     model_fall = YOLO(FALL_PATH)
#     model_fire = YOLO(FIRE_PATH)
#     model_face = YOLO(FACE_PATH)
#     model_headwear = YOLO(HEADWEAR_PATH)
#     liveness_tool = LivenessDetector()
    
#     print(f"Attempting to open camera source: {SOURCE}")
#     cap = cv2.VideoCapture(SOURCE)
    
#     if not cap.isOpened():
#         print(f"ERROR: Could not open video source {SOURCE}.")
#         return

#     # 1. Create a named window with the "NORMAL" flag (allows resizing)
#     cv2.namedWindow("Smart Surveillance System", cv2.WINDOW_NORMAL)

#     # 2. Force the window to a specific reasonable size (e.g., 1280x720)
#     cv2.resizeWindow("Smart Surveillance System", 1280, 720)

#     prev_time = 0

#     while True:
#         ret, frame = cap.read()
#         if not ret: break
        
#         # Create a clean copy for custom drawing (important!)
#         visual_frame = frame.copy()

#         new_time = time.time()
#         fps = 1/(new_time-prev_time)
#         prev_time = new_time

#         # --- 1. RUN MODELS ---
#         # pose_results = model_pose.track(frame, persist=True, verbose=False, device=0)[0]
#         pose_results = model_pose.track(
#             frame, 
#             persist=True, 
#             verbose=False, 
#             device=0,
#             tracker="bytetrack.yaml",  # Explicitly use ByteTrack (better than BoT-SORT for occlusion)
#             conf=0.65                   # Ignore low-confidence ghosts
#         )[0]
#         shoplift_results = model_shoplift(frame, verbose=False, device=0, conf=0.1)[0]
#         fall_results = model_fall(frame, verbose=False, device=0, conf=0.1)[0]
#         fire_results = model_fire(frame, verbose=False, device=0, conf=0.1)[0]
#         face_results = model_face(frame, verbose=False, device=0, conf=0.1)[0]
#         headwear_results = model_headwear(frame, verbose=False, device=0, conf=0.1)[0]

#         # We still need annotator for Fire/standard boxes
#         annotator = Annotator(visual_frame, line_width=2)
#         status = "SAFE"
#         label = ""
#         current_angle = 0

#         # --- DEBUGGING BLOCK (Put this before the 'for box in fire_results' loop) ---
#         print("Model Classes:", model_fire.names) 
#         # Output might be: {0: 'fire', 1: 'smoke', 2: 'other'} OR {0: 'other', 1: 'fire'...}
#         # ----------------------------------------------------------------------------

#         # --- 2. DETECT EVENTS (Updated for Fire vs Smoke) ---
#         fire_detected = False
#         smoke_detected = False
        
#         # Helper to get names {0:'fire', 1:'other', 2:'smoke'}
#         fire_names = model_fire.names 

#         for box in fire_results.boxes:
#             class_id = int(box.cls[0])
#             conf = float(box.conf[0])
#             class_name = fire_names[class_id]

#             # PRINT EVERY DETECTION TO TERMINAL
#             print(f"DEBUG FINDING: Found {class_name} with {conf*100:.1f}% confidence") 

#             if "fire" in class_name and conf > CONF_FIRE:
#                 fire_detected = True
#                 annotator.box_label(box.xyxy[0], f"FIRE {conf:.2f}", (0,0,255))
            
#             elif "smoke" in class_name and conf > CONF_SMOKE:
#                 smoke_detected = True
#                 annotator.box_label(box.xyxy[0], f"SMOKE {conf:.2f}", (0,140,255))

#         theft_boxes = []
#         for box in shoplift_results.boxes:
#             if float(box.conf[0]) > CONF_THEFT:
#                 theft_boxes.append(box.xyxy[0].cpu().numpy())

#         headwear_detected = False
#         for box in headwear_results.boxes:
#             if float(box.conf[0]) > CONF_HEADWEAR: headwear_detected = True

#         faces_detected = []
#         for box in face_results.boxes:
#             if float(box.conf[0]) > CONF_FACE:
#                 x1, y1, x2, y2 = map(int, box.xyxy[0])
#                 faces_detected.append((x1, y1, x2, y2))

#         # --- 3. INTELLIGENT FRAMING ---
#         if pose_results.boxes.id is not None:
#             track_ids = pose_results.boxes.id.int().cpu().tolist()
            
#             for i, box in enumerate(pose_results.boxes.xyxy):
#                 track_id = track_ids[i]
#                 bx1, by1, bx2, by2 = map(int, box)
#                 person_box = box.cpu().numpy()
                
#                 kpts = pose_results.keypoints[i].xy.cpu().numpy()[0]
#                 current_angle = liveness_tool.calculate_body_angle(kpts)
#                 annotator.kpts(pose_results.keypoints[i].data[0], shape=(640, 640), radius=4, kpt_line=True)
                
#                 has_face = False
#                 for (fx1, fy1, fx2, fy2) in faces_detected:
#                     if fx1 > bx1 and fx2 < bx2 and fy1 > by1 and fy2 < by2: has_face = True
                
#                 is_thief = False
#                 for t_box in theft_boxes:
#                     if calculate_iou(person_box, t_box) > 0.2: is_thief = True

#                 is_falling = False
#                 for fbox in fall_results.boxes:
#                     fbox_np = fbox.xyxy[0].cpu().numpy()
#                     if float(fbox.conf[0]) > CONF_FALL:
#                          if calculate_iou(person_box, fbox_np) > 0.3 and (current_angle > ANGLE_THRESH or current_angle == 0):
#                              is_falling = True
                
#                 final_color = (0, 255, 0)
#                 final_text = f"ID:{track_id}"

#                 if is_falling:
#                     final_color = (255, 0, 255)
#                     final_text = f"ID:{track_id} FALLING"
#                     status, label = "FALL", f"ID {track_id} FALL DETECTED"
#                 elif is_thief:
#                     final_color = (0, 165, 255)
#                     final_text = f"ID:{track_id} SUSPECT"
#                     # Only set theft if no critical event is active
#                     if status not in ["FALL", "FIRE", "SMOKE"]:
#                         status, label = "THEFT", f"ID {track_id} SUSPICIOUS"
#                 elif headwear_detected and not has_face:
#                     final_color = (0, 255, 255)
#                     final_text = f"ID:{track_id} HIDDEN"
#                     if status == "SAFE":
#                         status, label = "CONCEALED", f"ID {track_id} CHECK"
                
#                 draw_corner_rect(visual_frame, (bx1, by1), (bx2, by2), final_color)
#                 draw_text_inside(visual_frame, final_text, bx1, by1, final_color)

#         # --- 4. FINAL RENDERING & PRIORITY LOGIC ---
#         # Priority: FIRE > SMOKE > Fall > Theft
#         if fire_detected: 
#             status, label = "FIRE", "FIRE DETECTED"
#         elif smoke_detected and status != "FIRE": 
#             status, label = "SMOKE", "SMOKE DETECTED"

#         visual_frame = annotator.result() 
#         draw_hud(visual_frame, fps, status, label, current_angle)
        
#         if status != "SAFE":
#             save_evidence(visual_frame, status, label)
#             # This handles the Sound Logic (Alert for Fire, Silence for Smoke)
#             sound_system.trigger(status)

#         cv2.imshow("Smart Surveillance System", visual_frame)
#         if cv2.waitKey(1) & 0xFF == ord('q'): break

#     cap.release()
#     cv2.destroyAllWindows()

# if __name__ == "__main__":
#     main()