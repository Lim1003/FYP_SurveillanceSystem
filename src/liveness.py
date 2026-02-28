import numpy as np
import math

class LivenessDetector:
    def __init__(self):
        self.history = {} 

    def is_real_human(self, track_id, keypoints):
        # ... (Keep your existing liveness code here) ...
        # If you lost the previous code, just return True for now
        return True

    def calculate_body_angle(self, keypoints):
        """
        Calculates the angle of the spine relative to the vertical axis.
        Returns: Angle in degrees (0=Vertical, 90=Horizontal)
        """
        # YOLOv8 Pose Keypoints Map:
        # 5: Left Shoulder, 6: Right Shoulder
        # 11: Left Hip, 12: Right Hip
        
        # We need the "Center Shoulder" and "Center Hip" to draw the spine
        # keypoints is an array of shape (17, 2)
        
        l_shoulder = keypoints[5]
        r_shoulder = keypoints[6]
        l_hip = keypoints[11]
        r_hip = keypoints[12]

        # Check if confidence is low (coordinates are 0,0), if so, skip
        if np.sum(l_shoulder) == 0 or np.sum(l_hip) == 0:
            return 0 # Default to standing

        # Calculate midpoints
        mid_shoulder = (l_shoulder + r_shoulder) / 2
        mid_hip = (l_hip + r_hip) / 2

        # Calculate differences (delta)
        dy = mid_shoulder[1] - mid_hip[1] # Y difference
        dx = mid_shoulder[0] - mid_hip[0] # X difference

        # Calculate angle in radians using arctan2
        # We want the angle relative to the Y-axis (Vertical)
        angle_rad = math.atan2(abs(dx), abs(dy))
        angle_deg = math.degrees(angle_rad)

        return angle_deg