from flask import Flask, render_template, Response
import cv2
import numpy as np
import time
import datetime
import os
from threading import Thread, Lock

app = Flask(__name__)

# URL của camera
stream_url = 'http://192.168.137.107:4747/video/'
cap = cv2.VideoCapture(stream_url)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)

# Load Haar Cascade để phát hiện mắt
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

# Thông số
fps = 25
width, height = 320, 240
video_frame = None
lock = Lock()
capture_path = "captured_images"
os.makedirs(capture_path, exist_ok=True)

drowsy_frames = 0
FRAME_THRESHOLD = 15
EYE_AR_THRESH = 5  # Ngưỡng khoảng cách giữa mí trên và dưới
last_capture_time = None
capture_interval = 2

def camera_stream():
    global video_frame, drowsy_frames, last_capture_time
    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.05)
            continue
        
        frame = cv2.resize(frame, (width, height))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        eyes_detected = False
        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = frame[y:y+h, x:x+w]
            eyes = eye_cascade.detectMultiScale(roi_gray)
            
            eye_closed = False
            for (ex, ey, ew, eh) in eyes:
                eyes_detected = True
                if eh < EYE_AR_THRESH:  # Nếu mắt nhắm
                    cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (0, 0, 255), 2)  # Vẽ khung đỏ khi mắt nhắm
                    eye_closed = True
                else:
                    cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (0, 255, 0), 2)
            
            if eye_closed:
                drowsy_frames += 1
            else:
                drowsy_frames = 0
            
            if eyes_detected and drowsy_frames >= FRAME_THRESHOLD:
                current_time = datetime.datetime.now()
                if last_capture_time is None or (current_time - last_capture_time).total_seconds() > capture_interval:
                    last_capture_time = current_time
                    filename = current_time.strftime("%H-%M-%S_%d-%m-%Y") + ".jpg"
                    filepath = os.path.join(capture_path, filename)
                    cv2.imwrite(filepath, frame)
                    print(f"Drowsiness detected! Image saved as {filepath}")
                    drowsy_frames = 0  # Reset bộ đếm sau khi chụp
        
        with lock:
            video_frame = frame.copy() if frame is not None else None

def gen_frames():
    global video_frame
    while True:
        with lock:
            if video_frame is None:
                time.sleep(0.1)
                continue
            ret, buffer = cv2.imencode('.jpg', video_frame)
            if not ret:
                continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template('index_flask_server.html')

if __name__ == '__main__':
    camera_thread = Thread(target=camera_stream, daemon=True)
    camera_thread.start()
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    finally:
        if cap.isOpened():
            cap.release()
