from flask import Flask, render_template, Response
import cv2
import numpy as np
import time
import datetime
import os
from threading import Thread, Lock
import platform
from gtts import gTTS
import tempfile
import pygame
import threading
import sys
from PIL import ImageFont, ImageDraw, Image
import tensorflow as tf
tf.get_logger().setLevel('ERROR')
x
from tensorflow.keras.models import load_model

if platform.system() == "Windows":
    import winsound

app = Flask(__name__)

# Tải mô hình AI
drowsiness_model = load_model("drowsiness_model.h5")  # Dự đoán trạng thái mắt
sleepy_detection_model = load_model("sleepy_detection_model.h5")  # Dự đoán tư thế đầu

# Kết nối camera từ điện thoại
stream_url = 'http://192.168.137.162:4747/video/'
cap = cv2.VideoCapture(stream_url)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

fps = 25
width, height = 320, 240
video_frame = None
lock = Lock()
capture_path = "captured_images"
os.makedirs(capture_path, exist_ok=True)

ALERT_COOLDOWN = 5  
last_alert_time = 0  
pygame.mixer.init()

FONT_PATH = "arial.ttf"

def draw_text_vietnamese(img, text, position, color=(0, 255, 0)):
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    font = ImageFont.truetype(FONT_PATH, 24)
    draw.text(position, text, font=font, fill=color)
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

def play_alert_sound():
    global last_alert_time
    if time.time() - last_alert_time < ALERT_COOLDOWN:
        return  
    last_alert_time = time.time()
    sendWarning("Cảnh báo! Bạn đang buồn ngủ! Hãy nghỉ ngơi ngay.")

def sendWarning(text):
    def play_audio():
        try:
            tts = gTTS(text=text, lang="vi")
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio_file:
                temp_audio_path = temp_audio_file.name
                tts.save(temp_audio_path)
            pygame.mixer.music.load(temp_audio_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            pygame.mixer.music.stop()
            os.remove(temp_audio_path)
        except Exception as e:
            print(f"Lỗi âm thanh: {e}", file=sys.stderr)
    
    threading.Thread(target=play_audio, daemon=True).start()

def capture_image(frame):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(capture_path, f"alert_{timestamp}.jpg")
    cv2.imwrite(filename, frame)
    print(f"📸 Ảnh đã được lưu: {filename}")

def preprocess_face(face):
    try:
        face_resized = cv2.resize(face, (64, 64))  # Resize ảnh về 64x64
        face_resized = face_resized.astype("float32") / 255.0  # Chuẩn hóa dữ liệu
        face_resized = np.expand_dims(face_resized, axis=0)  # Thêm batch dimension
        return face_resized
    except Exception as e:
        print(f"⚠ Lỗi xử lý ảnh khuôn mặt: {e}")
        return None

def camera_stream():
    global video_frame, cap  
    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠ Mất kết nối camera, đang thử kết nối lại...")
            cap.release()
            time.sleep(2)
            cap = cv2.VideoCapture(stream_url)  
            continue

        frame = cv2.resize(frame, (width, height))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        if len(faces) == 0:
            with lock:
                video_frame = frame.copy()
            continue

        for (x, y, w, h) in faces:
            face_roi = frame[y:y+h, x:x+w]
            face_input = preprocess_face(face_roi)

            if face_input is None:
                continue  # Nếu lỗi xử lý ảnh, bỏ qua

            # **Dự đoán trạng thái mắt**
            eye_prediction = drowsiness_model.predict(face_input)
            eye_status = "Mắt mở" if eye_prediction[0][0] > 0.5 else "Mắt nhắm"

            # **Dự đoán tư thế đầu**
            head_prediction = sleepy_detection_model.predict(face_input)

            if head_prediction.shape[1] >= 4:
                head_prediction = np.squeeze(head_prediction)
                print("🔍 Head Prediction:", head_prediction)  

                head_status = "Tư thế bình thường"
                if head_prediction[1] > 0.6:
                    head_status = "Cúi gật đầu (Buồn ngủ)"
                elif head_prediction[2] > 0.6:
                    head_status = "Nghiêng trái (Buồn ngủ)"
                elif head_prediction[3] > 0.6:
                    head_status = "Nghiêng phải (Buồn ngủ)"
            else:
                head_status = "Không xác định"

            # Hiển thị kết quả lên màn hình
            frame = draw_text_vietnamese(frame, f"{eye_status}", (x, y-30), (0, 255, 0))
            frame = draw_text_vietnamese(frame, f"{head_status}", (x, y-10), (0, 255, 0))
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            # Nếu mắt nhắm hoặc tư thế đầu bất thường => Cảnh báo
            if "Mắt nhắm" in eye_status or "Buồn ngủ" in head_status:
                frame = draw_text_vietnamese(frame, "CẢNH BÁO: Ngủ gật!", (x, y-50), (0, 0, 255))
                play_alert_sound()
                capture_image(frame)

            break  # Chỉ xử lý khuôn mặt đầu tiên

        with lock:
            video_frame = frame.copy()

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
