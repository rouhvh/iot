from flask import Flask, render_template, Response
import cv2
from threading import Thread, Lock
import time
import datetime
import os

app = Flask(__name__)

# URL của luồng video và cấu hình các tham số
# stream_url = 'http://192.168.137.228:81/stream'
stream_url = 'http://192.168.137.107:4747/video/'

cap = cv2.VideoCapture(stream_url)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)  # Cấu hình kích thước bộ đệm để xử lý video mượt mà hơn

motion_detected = False
fps = 25  # Số khung hình trên giây
width = 320  # Giảm kích thước khung hình để xử lý nhanh hơn
height = 240

video_frame = None  # Biến để lưu trữ khung hình hiện tại
lock = Lock()  # Khóa để đảm bảo đồng bộ khi truy cập khung hình

# Đường dẫn để lưu trữ các hình ảnh được chụp
capture_path = "captured_images"
os.makedirs(capture_path, exist_ok=True)  # Tạo thư mục nếu chưa tồn tại

# Khởi tạo bộ trừ nền
fgbg = cv2.createBackgroundSubtractorMOG2()

# Các biến để điều khiển tần suất chụp ảnh
last_capture_time = None  # Thời gian chụp ảnh cuối cùng
capture_interval = 2  # Khoảng thời gian giữa các lần chụp ảnh (giây)
motion_threshold = 5000  # Diện tích contour tối thiểu để coi là chuyển động

# Hàm xử lý luồng video và phát hiện chuyển động
def camera_stream():
    global cap, video_frame, motion_detected, last_capture_time
    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.05)  # Chờ một chút trước khi thử lại nếu không đọc được khung hình
            continue

        # Thay đổi kích thước khung hình để xử lý nhanh hơn
        frame = cv2.resize(frame, (width, height))

        # Áp dụng trừ nền
        fgmask = fgbg.apply(frame)
        # Tìm các contour trong mặt nạ
        contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Kiểm tra chuyển động
        if any(cv2.contourArea(contour) > motion_threshold for contour in contours):
            motion_detected = True
            current_time = datetime.datetime.now()

            # Lưu khung hình dưới dạng ảnh nếu khoảng thời gian đã đủ
            if last_capture_time is None or (current_time - last_capture_time).total_seconds() > capture_interval:
                last_capture_time = current_time
                filename = current_time.strftime("%H-%M-%S_%d-%m-%Y") + ".jpg"
                filepath = os.path.join(capture_path, filename)
                cv2.imwrite(filepath, frame)
                print(f"Motion detected! Image saved as {filepath}")
        else:
            motion_detected = False

        with lock:
            video_frame = frame.copy() if frame is not None else None

# Hàm tạo khung hình để gửi tới client
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

# Định tuyến Flask để truyền luồng video tới client
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Định tuyến Flask để phục vụ trang HTML chính
@app.route('/')
def index():
    return render_template('index_flask_server.html')

# Hàm để tắt máy chủ Flask
def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

# Định tuyến Flask để tắt máy chủ
@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

# Hàm chính để chạy ứng dụng Flask và xử lý luồng video
if __name__ == '__main__':
    camera_thread = Thread(target=camera_stream, daemon=True)
    camera_thread.start()
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    finally:
        if cap.isOpened():
            cap.release()
