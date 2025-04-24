import os
import time

import cv2
import mediapipe as mp
from dotenv import load_dotenv
from flask import Flask, Response, jsonify
from flask_cors import CORS
from twilio.rest import Client  # <-- Twilio import

app = Flask(__name__)
CORS(app)
# MediaPipe setup
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

fall_detected = False
fall_confirmed = False
fall_start_time = None
fall_confirmation_threshold = 3  # seconds

TWILIO_ACCOUNT_SID = 'AC38642c2c2c680a3aee0634e1ad20354b'
TWILIO_AUTH_TOKEN = 'bda1c0dc0a08153e5b42e8435a147e6a'
TWILIO_FROM_NUMBER = '+19705729437'
TWILIO_TO_NUMBER = '+918076061427'


twilio_client = Client(TWILIO_ACCOUNT_SID,TWILIO_AUTH_TOKEN)

def send_fall_alert():
    try:
        message = twilio_client.messages.create(
            body="🚨 Fall confirmed! Please check immediately!",
            from_=TWILIO_FROM_NUMBER,
            to=TWILIO_TO_NUMBER
        )
        print("✅ Twilio alert sent! SID:", message.sid)
    except Exception as e:
        print("❌ Failed to send Twilio alert:", str(e))

def detect_fall(frame):
    global fall_detected, fall_confirmed, fall_start_time

    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)

    if not results.pose_landmarks:
        fall_start_time = None
        fall_confirmed = False
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

    fall_detected = vertical_diff < 0.1

    if fall_detected:
        if fall_start_time is None:
            fall_start_time = time.time()
        elif time.time() - fall_start_time >= fall_confirmation_threshold and not fall_confirmed:
            fall_confirmed = True
            send_fall_alert()
    else:
        fall_start_time = None
        fall_confirmed = False

    return fall_detected

# Set up the camera with wider resolution
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break

        detect_fall(frame)

        # Draw pose landmarks
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        # Status display
        status_text = "FALL CONFIRMED" if fall_confirmed else "FALL DETECTED" if fall_detected else "NORMAL"
        color = (0, 0, 255) if fall_confirmed else (0, 255, 255) if fall_detected else (0, 255, 0)
        cv2.putText(frame, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

        # Encode frame
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/fall_status')
def fall_status():
    return jsonify({
        "fall_detected": fall_detected,
        "fall_confirmed": fall_confirmed
    })

if __name__ == '__main__':
    app.run(debug=True)
