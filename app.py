from flask import Flask, render_template, Response, request
import os
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

import cv2
import numpy as np
import time
import threading
import datetime
import winsound
import base64
import psutil
import torch
import gc
from concurrent.futures import ThreadPoolExecutor
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator, colors
from src.liveness import LivenessDetector
from src.reid import PersonReID

import firebase_admin
from firebase_admin import credentials, db
from werkzeug.utils import secure_filename

# ==========================================
#        CONFIGURATION & SETUP
# ==========================================

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- GLOBAL VARIABLES ---
dashboard_state = {"alerts": []}
loaded_models = {}  
reid_system = None
last_upload_times = {} 

# Sensitivity Thresholds
CONF_THEFT     = 0.75
CONF_FIRE      = 0.60
CONF_SMOKE     = 0.60 
CONF_FALL      = 0.85
CONF_FACE      = 0.60
CONF_HEADWEAR  = 0.70
ANGLE_THRESH   = 50
COOLDOWN_SEC   = 3.0
SOUND_COOLDOWN = 3.0

# --- FIREBASE INIT ---
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://smartsurveillance-8c28d-default-rtdb.asia-southeast1.firebasedatabase.app/'
        })
    ref = db.reference('anomalies')
    print("--- FIREBASE CONNECTED ---")
except Exception as e:
    print(f"--- FIREBASE ERROR: {e} ---")

# ==========================================
#        LAG-FREE CAMERA CLASS (UPDATED)
# ==========================================
class ThreadedCamera:
    """
    Reads frames in a separate thread.
    Forces TCP to prevent packet loss (Green/Grey artifacts).
    """
    def __init__(self, src=0):
        self.src = src
        
        # [FORCE TCP] This is the critical fix for RTSP artifacts
        if isinstance(src, str) and src.startswith("rtsp"):
            # Use FFMPEG backend with explicit TCP transport
            self.cap = cv2.VideoCapture(self.src, cv2.CAP_FFMPEG)
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))
            # Force TCP (Wait for packets instead of dropping them)
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp" 
        else:
            self.cap = cv2.VideoCapture(self.src)

        # Limit internal buffer to 1 frame (Reduces Latency)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        self.grabbed, self.frame = self.cap.read()
        self.started = False
        self.read_lock = threading.Lock()

    def start(self):
        if self.started: return None
        self.started = True
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True 
        self.thread.start()
        return self

    def update(self):
        while self.started:
            grabbed, frame = self.cap.read()
            with self.read_lock:
                self.grabbed = grabbed
                self.frame = frame
            # Tiny sleep to prevent CPU overheating
            time.sleep(0.005)

    def read(self):
        with self.read_lock:
            if not self.grabbed:
                return False, None
            return True, self.frame.copy()

    def stop(self):
        self.started = False
        if self.thread.is_alive():
            self.thread.join()
        self.cap.release()
        
    def isOpened(self):
        return self.cap.isOpened()

# ==========================================
#        SOUND & UPLOAD SYSTEMS
# ==========================================

class SoundAlertSystem:
    def __init__(self):
        self.last_alert_time = 0
        
    def trigger(self, status):
        current_time = time.time()
        if current_time - self.last_alert_time < SOUND_COOLDOWN:
            return

        try:
            if status == "FIRE":
                winsound.PlaySound("SystemHand", winsound.SND_ALIAS | winsound.SND_ASYNC)
            elif status == "FALL":
                winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)
            elif status == "THEFT":
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
            self.last_alert_time = current_time
        except:
            pass 

sound_system = SoundAlertSystem()

def upload_worker(frame, filename, metadata, session_id):
    try:
        _, buffer = cv2.imencode('.jpg', frame)
        base64_str = base64.b64encode(buffer).decode('utf-8')
        base64_image = f"data:image/jpeg;base64,{base64_str}"
        metadata["image_url"] = base64_image
        
        ref.child(session_id).push(metadata)
        print(f"[DB] Saved to folder: {session_id}")
    except Exception as e:
        print(f"[DB] Save Failed: {e}")

def trigger_upload(frame, event_type, track_id, confidence, session_id="General"):
    current_time = time.time()
    key = f"{event_type}_{track_id}" if track_id else f"GLOBAL_{event_type}"

    if key in last_upload_times:
        if current_time - last_upload_times[key] < COOLDOWN_SEC:
            return

    last_upload_times[key] = current_time

    timestamp_str = datetime.datetime.now().strftime("%H:%M:%S")
    full_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"{event_type}_{int(time.time())}.jpg"

    metadata = {
        "event": event_type,
        "person_id": str(track_id) if track_id else "N/A",
        "confidence": float(confidence),
        "timestamp": full_timestamp,
        "time_short": timestamp_str,
        "location": "Main Camera",
        "session_id": session_id
    }

    dashboard_state["alerts"].insert(0, metadata)
    if len(dashboard_state["alerts"]) > 50:
        dashboard_state["alerts"].pop()

    thread = threading.Thread(target=upload_worker, args=(frame.copy(), filename, metadata, session_id))
    thread.start()

# ==========================================
#        VISUALIZATION HELPERS
# ==========================================

def draw_corner_rect(img, pt1, pt2, color, corner_thickness=5, connect_thickness=1):
    x1, y1 = pt1
    x2, y2 = pt2
    cv2.rectangle(img, pt1, pt2, color, connect_thickness)
    length = min(abs(x2-x1), abs(y2-y1)) * 0.2
    l = int(max(length, 20)) 
    cv2.line(img, (x1, y1), (x1 + l, y1), color, corner_thickness)
    cv2.line(img, (x1, y1), (x1, y1 + l), color, corner_thickness)
    cv2.line(img, (x2, y1), (x2 - l, y1), color, corner_thickness)
    cv2.line(img, (x2, y1), (x2, y1 + l), color, corner_thickness)
    cv2.line(img, (x1, y2), (x1 + l, y2), color, corner_thickness)
    cv2.line(img, (x1, y2), (x1, y2 - l), color, corner_thickness)
    cv2.line(img, (x2, y2), (x2 - l, y2), color, corner_thickness)
    cv2.line(img, (x2, y2), (x2, y2 - l), color, corner_thickness)

def draw_text_inside(img, text, x1, y1, color):
    pad_x, pad_y = 10, 25
    font_scale = 0.6
    cv2.putText(img, text, (x1 + pad_x, y1 + pad_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0,0,0), 3)
    cv2.putText(img, text, (x1 + pad_x, y1 + pad_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2)

def draw_hud(frame, fps, status, label, angle):
    height, width = frame.shape[:2]
    scale = height / 720.0
    font_scale_main = max(0.5, 0.7 * scale)
    margin_x, pos_y1, pos_y2 = int(10*scale), int(30*scale), int(60*scale)

    if status == "FIRE":       color, text = (0, 0, 255), f"DANGER: {label}"
    elif status == "SMOKE":    color, text = (0, 140, 255), f"WARNING: {label}"
    elif status == "FALL":     color, text = (255, 0, 255), f"MEDICAL: {label}"
    elif status == "THEFT":    color, text = (0, 165, 255), f"SECURITY: {label}"
    elif status == "CONCEALED":color, text = (0, 255, 255), f"CAUTION: {label}"
    else:                      color, text = (0, 255, 0), "SYSTEM NORMAL"

    cv2.putText(frame, text, (margin_x, pos_y1), cv2.FONT_HERSHEY_SIMPLEX, font_scale_main, (0,0,0), 4)
    cv2.putText(frame, text, (margin_x, pos_y1), cv2.FONT_HERSHEY_SIMPLEX, font_scale_main, color, 2)
    stats = f"FPS: {fps:.1f} | Angle: {int(angle)}deg"
    cv2.putText(frame, stats, (margin_x, pos_y2), cv2.FONT_HERSHEY_SIMPLEX, font_scale_main*0.7, (255,255,255), 1)

def calculate_iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    return intersection / box1_area if box1_area > 0 else 0

# ==========================================
#        MEMORY & MODEL MANAGEMENT
# ==========================================

MODEL_PATHS = {
    'pose': 'yolov8m-pose.pt',
    'shoplift': 'Smart_Surveillance_FYP_Train/shoplifting_tuned_v1/weights/best.pt', 
    'fall': 'Smart_Surveillance_FYP_Train/fall_tuned_v1/weights/best.pt',
    'fire': 'Smart_Surveillance_FYP_Train/fire_tuned_v1/weights/best.pt',
    'face': 'Smart_Surveillance_FYP_Train/face_model/weights/best.pt',
    'headwear': 'Smart_Surveillance_FYP_Train/headwear_tuned_v1/weights/best.pt'
}

def load_required_models(selected_list):
    global loaded_models, reid_system
    
    if reid_system is None:
        try:
            reid_system = PersonReID()
        except Exception as e:
            print(f"[WARNING] ReID Init Failed: {e}. ReID features will be disabled.")
            reid_system = None

    if 'pose' not in loaded_models:
        print("[GPU] Loading Pose Model...")
        loaded_models['pose'] = YOLO(MODEL_PATHS['pose'])
    
    model_keys = ['fire', 'fall', 'shoplift', 'face', 'headwear']
    memory_changed = False

    for key in model_keys:
        if key in selected_list and key not in loaded_models:
            print(f"[GPU] Loading {key} model...")
            loaded_models[key] = YOLO(MODEL_PATHS[key])
            memory_changed = True
        elif key not in selected_list and key in loaded_models:
            print(f"[GPU] Offloading {key} model...")
            del loaded_models[key]
            memory_changed = True
    
    if memory_changed:
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            print(f"[GPU] Cache Cleared.")

def clear_all_memory():
    global loaded_models
    loaded_models.clear()
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    print("[GPU] All Models Offloaded.")

def run_model_inference(model_key, frame):
    if model_key in loaded_models:
        return loaded_models[model_key](frame, verbose=False, conf=0.1)[0]
    return None

# ==========================================
#        MAIN LOGIC LOOP
# ==========================================

def generate_frames(selected_models, source=0, session_id="General"):
    load_required_models(selected_models)
    liveness_tool = LivenessDetector()
    
    # 1. SETUP SOURCE (With Logic for Threading)
    is_live = False
    
    if isinstance(source, str) and source.isdigit():
        source = int(source)
        is_live = True 
    elif isinstance(source, str) and (source.startswith('rtsp') or source.startswith('http')):
        is_live = True 
        
    # Start Camera (TCP Enabled for RTSP)
    if is_live:
        print(f"[STREAM] Starting Threaded Camera for: {source}")
        cap = ThreadedCamera(source).start()
    else:
        print(f"[STREAM] Starting File Stream for: {source}")
        cap = cv2.VideoCapture(source)
    
    if not cap.isOpened():
        print(f"[ERROR] Could not open video source: {source}")
        err_img = np.zeros((720, 1280, 3), np.uint8)
        cv2.putText(err_img, "ERROR: CAMERA NOT FOUND", (350, 360), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,0,255), 3)
        _, buf = cv2.imencode('.jpg', err_img)
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n')
        return

    executor = ThreadPoolExecutor(max_workers=4)
    fps = 0 

    while True:
        # 2. Read Frame
        if is_live:
            success, frame = cap.read()
        else:
            success, frame = cap.read()
            
        if not success:
            if is_live:
                print("[STREAM] Signal Lost. Retrying...")
                time.sleep(1)
                continue 
            else:
                # File Finished
                blank = np.zeros((720, 1280, 3), np.uint8)
                cv2.putText(blank, "PLAYBACK FINISHED", (400, 360), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,255,0), 3)
                _, buf = cv2.imencode('.jpg', blank)
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n')
                time.sleep(0.1)
                continue

        t0 = time.time()
        visual_frame = frame.copy()
        
        # --- PARALLEL INFERENCE ---
        futures = {}
        for key in ['fire', 'shoplift', 'fall', 'face', 'headwear']:
            if key in selected_models:
                futures[key] = executor.submit(run_model_inference, key, frame)
        
        # [FIX] Added conf=0.65 to stop drawing skeletons on fire/smoke
        pose_results = loaded_models['pose'].track(frame, persist=True, verbose=False, tracker="bytetrack.yaml", conf=0.65)[0]
        results = {key: future.result() for key, future in futures.items()}

        annotator = Annotator(visual_frame, line_width=2)
        status = "SAFE"
        label = ""
        current_angle = 0
        fire_detected = False
        smoke_detected = False
        
        # 1. Process Fire
        if 'fire' in results and results['fire']:
            fire_names = loaded_models['fire'].names
            for box in results['fire'].boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                name = fire_names[cls_id]
                
                if "fire" in name and conf > CONF_FIRE:
                    fire_detected = True
                    annotator.box_label(box.xyxy[0], f"FIRE {conf:.2f}", (0,0,255))
                elif "smoke" in name and conf > CONF_SMOKE:
                    smoke_detected = True
                    annotator.box_label(box.xyxy[0], f"SMOKE {conf:.2f}", (0,140,255))

        # 2. Process People
        if pose_results.boxes.id is not None:
            track_ids = pose_results.boxes.id.int().cpu().tolist()
            used_ids_in_frame = set() 
            
            # [UPDATED] Store (Box, Confidence) tuples instead of just Box
            shoplift_data = []
            if 'shoplift' in results:
                for b in results['shoplift'].boxes:
                    if b.conf[0] > CONF_THEFT:
                        shoplift_data.append((b.xyxy[0].cpu().numpy(), float(b.conf[0])))

            faces = []
            if 'face' in selected_models or 'headwear' in selected_models:
                if 'face' in results and results['face']:
                    faces = [(int(b.xyxy[0][0]), int(b.xyxy[0][1]), int(b.xyxy[0][2]), int(b.xyxy[0][3])) for b in results['face'].boxes if b.conf[0] > CONF_FACE]

            # [UPDATED] Store headwear confidence
            headwear_conf = 0.0
            if 'headwear' in results and results['headwear']:
                for b in results['headwear'].boxes:
                    if b.conf[0] > CONF_HEADWEAR:
                        headwear_conf = float(b.conf[0]) # Get the highest confidence

            for i, box in enumerate(pose_results.boxes.xyxy):
                person_box = box.cpu().numpy()
                
                # [SAFETY CHECK] If Person Box is inside a Fire Box, ignore it (It's a Ghost)
                is_ghost = False
                if 'fire' in results and results['fire']:
                    for fire_box in results['fire'].boxes.xyxy:
                        if calculate_iou(person_box, fire_box.cpu().numpy()) > 0.6:
                            is_ghost = True
                
                if is_ghost: continue # Skip drawing this skeleton
                yolo_id = track_ids[i]
                
                # ReID Check
                if reid_system:
                    try:
                        final_id = reid_system.resolve_id(yolo_id, frame, box.cpu().numpy(), used_ids_in_frame)
                        used_ids_in_frame.add(final_id)
                    except:
                        final_id = yolo_id
                else:
                    final_id = yolo_id
                
                kpts = pose_results.keypoints[i].xy.cpu().numpy()[0]
                current_angle = liveness_tool.calculate_body_angle(kpts)
                annotator.kpts(pose_results.keypoints[i].data[0], shape=(640, 640), radius=4, kpt_line=True)

                person_box = box.cpu().numpy()
                bx1, by1, bx2, by2 = map(int, box)

                has_face = False
                for (fx1, fy1, fx2, fy2) in faces:
                    if fx1 > bx1 and fx2 < bx2 and fy1 > by1 and fy2 < by2: has_face = True
                
                # [UPDATED] Check theft and get confidence
                is_thief = False
                theft_conf = 0.0
                for (t_box, t_conf) in shoplift_data:
                    if calculate_iou(person_box, t_box) > 0.2: 
                        is_thief = True
                        theft_conf = t_conf

                # [UPDATED] Check fall and get confidence
                is_falling = False
                fall_conf = 0.0
                if 'fall' in results and results['fall']:
                    for fbox in results['fall'].boxes:
                        f_np = fbox.xyxy[0].cpu().numpy()
                        f_c = float(fbox.conf[0])
                        if f_c > CONF_FALL:
                            if calculate_iou(person_box, f_np) > 0.3 and (current_angle > ANGLE_THRESH or current_angle == 0):
                                is_falling = True
                                fall_conf = f_c

                final_color = (0, 255, 0)
                final_text = f"ID:{final_id}"

                # --- LOGIC & DRAWING ORDER FIX ---
                trigger_event = None # Store event to upload AFTER drawing

                if is_falling:
                    final_color = (255, 0, 255)
                    # [UPDATED] Added {fall_conf:.2f}
                    final_text = f"ID:{final_id} FALLING {fall_conf:.2f}"
                    status, label = "FALL", f"ID {final_id}"
                    trigger_event = ("FALL", fall_conf)

                elif is_thief:
                    final_color = (0, 165, 255)
                    # [UPDATED] Added {theft_conf:.2f}
                    final_text = f"ID:{final_id} SUSPECT {theft_conf:.2f}"
                    if status not in ["FALL", "FIRE", "SMOKE"]:
                        status, label = "THEFT", f"ID {final_id}"
                        trigger_event = ("THEFT", theft_conf)

                elif headwear_conf > 0 and not has_face and 'headwear' in selected_models:
                    final_color = (0, 255, 255)
                    # [UPDATED] Added {headwear_conf:.2f}
                    final_text = f"ID:{final_id} HIDDEN {headwear_conf:.2f}"
                    if status == "SAFE":
                        status, label = "CONCEALED", f"ID {final_id}"
                        trigger_event = ("CONCEALED_ID", headwear_conf)
                
                # 1. DRAW FIRST (Crucial: Box must exist on frame before upload)
                draw_corner_rect(visual_frame, (bx1, by1), (bx2, by2), final_color)
                draw_text_inside(visual_frame, final_text, bx1, by1, final_color)

                # 2. TRIGGER UPLOAD (Now frame has the drawing)
                if trigger_event:
                    trigger_upload(visual_frame, trigger_event[0], final_id, trigger_event[1], session_id)

        if fire_detected:
            status, label = "FIRE", "FIRE DETECTED"
            trigger_upload(visual_frame, "FIRE", None, 0.99, session_id)
        elif smoke_detected and status != "FIRE":
            status, label = "SMOKE", "SMOKE DETECTED"
            trigger_upload(visual_frame, "SMOKE", None, 0.80, session_id)

        if status != "SAFE":
            sound_system.trigger(status)

        if time.time() - t0 > 0:
            fps = 1/(time.time() - t0)

        draw_hud(visual_frame, fps, status, label, current_angle)
        
        ret, buffer = cv2.imencode('.jpg', visual_frame)
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    
    if is_live:
        cap.stop()
    else:
        cap.release()

# ==========================================
#        FLASK ROUTES
# ==========================================

@app.route('/')
def index(): return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    source = request.args.get('source', 0)
    models = request.args.get('models', '').split(',')
    session = request.args.get('session', 'General')
    return Response(generate_frames(models, source, session), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'video' not in request.files: return {'error': 'No file part'}, 400
    file = request.files['video']
    if file.filename == '': return {'error': 'No selected file'}, 400
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return {'filepath': filepath.replace('\\', '/')}, 200

@app.route('/api/dashboard_data')
def get_dashboard_data():
    return dashboard_state

@app.route('/api/reset_session', methods=['POST'])
def reset_session():
    clear_all_memory()
    dashboard_state['alerts'] = []
    return {'status': 'cleared'}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, threaded=True)