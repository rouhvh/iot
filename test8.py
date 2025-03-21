from flask import Flask, render_template, Response
import cv2
import numpy as np
import time
import datetime
import os
from threading import Thread, Lock
from playsound import playsound
import platform
from gtts import gTTS
import tempfile
import pygame
import threading
import sys
from PIL import ImageFont, ImageDraw, Image

if platform.system() == "Windows":
    import winsound

app = Flask(__name__)

stream_url = 'http://192.168.137.162:4747/video/'
cap = cv2.VideoCapture(stream_url)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

fps = 25
width, height = 320, 240
video_frame = None
lock = Lock()
capture_path = "captured_images"
os.makedirs(capture_path, exist_ok=True)

EYE_CLOSED_DURATION_THRESHOLD = 2
EYE_PIXEL_THRESHOLD = 15
closed_start_time = None

alert_audio = "alarm.mp3"
FONT_PATH = "arial.ttf"

alert_playing = False
last_alert_time = 0
ALERT_COOLDOWN = 5  

pygame.mixer.init()

def draw_text_vietnamese(img, text, position, color=(0, 255, 0)):
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    font = ImageFont.truetype(FONT_PATH, 24)
    draw.text(position, text, font=font, fill=color)
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

def play_alert_sound():
    global alert_playing, last_alert_time
    if time.time() - last_alert_time < ALERT_COOLDOWN:
        return  
    last_alert_time = time.time()
    try:
        if os.path.exists(alert_audio):
            playsound(alert_audio)
        else:
            print("⚠ Không tìm thấy file âm thanh, phát beep thay thế.")
            if platform.system() == "Windows":
                winsound.Beep(1000, 500)
    except Exception as e:
        print("Lỗi khi phát âm thanh cảnh báo:", e)
    finally:
        alert_playing = False

def sendWarning(text):
    global alert_playing, last_alert_time
    if alert_playing or (time.time() - last_alert_time < ALERT_COOLDOWN):
        return  
    alert_playing = True
    
    def play_audio():
        global alert_playing
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
            os.remove(temp_audio_path)  # Chỉ xóa sau khi nhạc phát xong
        except Exception as e:
            print(f"Lỗi âm thanh: {e}", file=sys.stderr)
        finally:
            alert_playing = False
    
    threading.Thread(target=play_audio, daemon=True).start()

def capture_image(frame):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(capture_path, f"alert_{timestamp}.jpg")
    cv2.imwrite(filename, frame)
    print(f"📸 Ảnh đã được lưu: {filename}")

def reconnect_camera():
    global cap
    cap.release()
    time.sleep(2)
    cap = cv2.VideoCapture(stream_url)

def camera_stream():
    global video_frame, closed_start_time
    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠ Mất kết nối camera, đang thử kết nối lại...")
            reconnect_camera()
            time.sleep(0.5)
            continue

        frame = cv2.resize(frame, (width, height))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
        
        eye_closed = False  # Trạng thái chung của mắt

        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = frame[y:y+h, x:x+w]
            # Phát hiện mắt
            eyes = eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=5)
            if len(eyes) == 0:
                # Nếu không dò được mắt nào, giả sử mắt đóng
                eyes_detected = True
                eye_closed = True
                # Vẽ ước lượng vùng mắt (ở phần trên của khuôn mặt)
                cv2.rectangle(roi_color, (int(w*0.25), int(h*0.25)), (int(w*0.75), int(h*0.5)), (0, 0, 255), 2)
            else:
                eyes_detected = True
                closed_count = 0
                for (ex, ey, ew, eh) in eyes:
                    if eh < EYE_PIXEL_THRESHOLD:
                        closed_count += 1
                        cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (0, 0, 255), 2)  # Vẽ khung đỏ cho mắt đóng
                    else:
                        cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (0, 255, 0), 2)  # Vẽ khung xanh cho mắt mở
                # Chỉ coi là mắt đóng nếu tất cả các mắt đều đóng
                if len(eyes) > 0 and closed_count == len(eyes):
                    eye_closed = True
                else:
                    eye_closed = False
            # Xử lý chỉ khuôn mặt đầu tiên
            break


        eyes_detected = False
        eye_closed = False  
        show_warning = False  

        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = frame[y:y+h, x:x+w]

            eyes = eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=5)
            if len(eyes) == 0:
                eyes_detected = True
                eye_closed = True
            else:
                eyes_detected = True
                closed_count = sum(1 for (ex, ey, ew, eh) in eyes if eh < EYE_PIXEL_THRESHOLD)
                eye_closed = closed_count == len(eyes)
            break  

        current_time = time.time()
        if eyes_detected and eye_closed:
            if closed_start_time is None:
                closed_start_time = current_time
            elif current_time - closed_start_time >= EYE_CLOSED_DURATION_THRESHOLD:
                show_warning = True  
        else:
            closed_start_time = None

        for (x, y, w, h) in faces:
            if eye_closed:
                if show_warning:
                    frame = draw_text_vietnamese(frame, "NGUY HIỂM!", (x + 5, y - 10), (0, 0, 255))
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                    sendWarning("ALO ALO ALO! Hãy tỉnh táo!")
                    capture_image(frame)  
                else:
                    frame = draw_text_vietnamese(frame, "Mắt đang nhắm!", (x + 5, y - 10), (0, 0, 255))
            else:
                frame = draw_text_vietnamese(frame, "Mắt đang mở!", (x + 5, y - 10), (0, 255, 0))

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
