# import math
# import time

# import cv2
# import mediapipe as mp

# # Initialize MediaPipe Pose
# mp_pose = mp.solutions.pose
# pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)
# mp_drawing = mp.solutions.drawing_utils

# # Function to detect fall using body posture (lying down horizontally)
# def detect_fall(frame):
#     image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     results = pose.process(image_rgb)

#     if not results.pose_landmarks:
#         return False

#     # Extract key landmarks: left/right shoulder and left/right hip
#     landmarks = results.pose_landmarks.landmark

#     try:
#         left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
#         right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
#         left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
#         right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
#     except IndexError:
#         return False

#     # Compute average shoulder and hip y-positions
#     shoulder_y_avg = (left_shoulder.y + right_shoulder.y) / 2
#     hip_y_avg = (left_hip.y + right_hip.y) / 2

#     # Check if the vertical distance is too small = person is more horizontal
#     vertical_diff = abs(shoulder_y_avg - hip_y_avg)

#     return vertical_diff < 0.1  # adjust threshold based on testing

# # Timing variables
# fall_detected = False
# fall_start_time = None
# fall_confirmed = False
# fall_confirmation_threshold = 3  # seconds

# # Capture video
# cap = cv2.VideoCapture(0)  # or 'video.mp4'

# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break

#     frame = cv2.resize(frame, (640, 480))

#     # Run MediaPipe-based fall detection
#     fall_detected = detect_fall(frame)

#     # Fall confirmation logic
#     if fall_detected:
#         if fall_start_time is None:
#             fall_start_time = time.time()
#         elif time.time() - fall_start_time >= fall_confirmation_threshold and not fall_confirmed:
#             print("✅ FALL CONFIRMED!")
#             fall_confirmed = True
#     else:
#         fall_start_time = None
#         fall_confirmed = False

#     # Draw landmarks for visualization
#     image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     results = pose.process(image_rgb)
#     if results.pose_landmarks:
#         mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

#     # Display status
#     status_text = "FALL CONFIRMED!" if fall_confirmed else ("FALL DETECTED" if fall_detected else "Normal")
#     color = (0, 0, 255) if fall_confirmed else (0, 255, 255) if fall_detected else (0, 255, 0)
#     cv2.putText(frame, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
#     cv2.imshow("Fall Detection", frame)

#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()

import cv2
# fall.py
import mediapipe as mp

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)

def detect_fall(frame):
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)

    if not results.pose_landmarks:
        return False

    try:
        landmarks = results.pose_landmarks.landmark
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
    except IndexError:
        return False

    shoulder_y_avg = (left_shoulder.y + right_shoulder.y) / 2
    hip_y_avg = (left_hip.y + right_hip.y) / 2
    vertical_diff = abs(shoulder_y_avg - hip_y_avg)

    return vertical_diff < 0.1
