BÁO CÁO HỆ THỐNG phát hiện tình trạng buồn ngủ khi lái xe oto và cảnh báo người lái xe
![image](https://github.com/user-attachments/assets/d1572174-b9a5-44f7-b7c8-769db9bdac3e)
Trong bối cảnh giao thông ngày càng trở nên phức tạp và số lượng tai nạn giao thông liên quan đến người lái xe buồn ngủ ngày càng gia tăng, việc phát triển các hệ thống hỗ trợ an toàn cho người lái xe là một nhu cầu cấp thiết. Một trong những nguyên nhân chính dẫn đến tai nạn giao thông là tình trạng buồn ngủ của người lái xe, đặc biệt là trong các chuyến đi dài hoặc vào ban đêm. Để giải quyết vấn đề này, công nghệ nhận diện hình ảnh và trí tuệ nhân tạo đã mở ra những khả năng mới trong việc phát hiện và cảnh báo tình trạng buồn ngủ của người lái xe.
Dự án "Phát hiện tình trạng buồn ngủ khi lái xe oto và cảnh báo người lái xe" nhằm xây dựng một hệ thống có khả năng nhận diện khi mắt người lái xe đóng liên tục trong một khoảng thời gian nhất định, qua đó đưa ra các cảnh báo kịp thời để đảm bảo sự an toàn. Hệ thống sử dụng công nghệ xử lý hình ảnh với OpenCV để phát hiện khuôn mặt và mắt của người lái xe, kết hợp với các thuật toán xử lý để xác định tình trạng buồn ngủ. Khi phát hiện dấu hiệu buồn ngủ, hệ thống sẽ tự động chụp ảnh và phát cảnh báo bằng âm thanh hoặc giọng nói.


📌 Giới thiệu hệ thống  
Hệ thống phát tình trạng buồn ngủ của tài xế khi tham gia giao thông và phát cảnh báo bằng âm thanh . Hệ thống có khả năng:
- 📸 Nhận diện tình trạng buồn ngủ của các tài xế khi lái xe 
- 🔍 Cảnh báo kịp thời khi tài xế có giấu hiệu ngủ quên khi tham gia giao thông
- 📊 Lưu trữ dữ liệu vi phạm vào cơ sở dữ liệu


 🏗️ Cấu trúc hệ thống
Hệ thống bao gồm các thành phần chính:
Camera giám sát: Ghi lại hình ảnh của tài xế khi lái xe.
Xử lý ảnh & AI: Phát hiện trạng thái buồn ngủ và nhận diện khuôn mặt.
Cơ sở dữ liệu: Lưu thông tin trạng thái của tài xế để phân tích và đánh giá.

![image](https://github.com/user-attachments/assets/7e0b9c63-31e6-4ae7-8ac5-6749f4f6bf2a)

   
 🛠️ Công cụ sử dụng
Ngôn ngữ lập trình: Python 🐍 (OpenCV, YOLO, Pytesseract, SQLite)
Thư viện hỗ trợ: Numpy, Pandas, ultralytics...
Cơ sở dữ liệu: SQLite/MySQL
Mô hình AI: YOLOv8 để nhận diện khuôn mặt và trạng thái mắt


 🚀 Hướng dẫn cài đặt và chạy
 
 1 Cài đặt thư viện
 
 python 3.7+
 
 Sau đó cài đặt các thư viện trong file requirements.txt với câu lệnh sau
```bash
pip install -r requirements.txt
```
2 Tạo môi truờng ảo(tùy chọn)
``` bash
python -m venv venv
source venv/bin/activate  # Trên macOS/Linux
.\venv\Scripts\activate  # Trên Windows
```
3 Tạo cơ sở dữ liệu
``` bash
conn = sqlite3.connect("violations.db")
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_type TEXT,
                timestamp TEXT)''')
conn.commit()
```
 4 Chạy hệ thống
```bash
python traffic_violation_detection.py
```

📖 Hướng dẫn sử dụng
1. Mở giao diện hệ thống trên trình duyệt web.
2. Kết nối camera giám sát để theo dõi tình trạng tài xế.
3. Hệ thống sẽ tự động giám sát và cảnh báo khi phát hiện tài xế có dấu hiệu buồn ngủ.
4. Dữ liệu vi phạm sẽ được lưu trữ vào cơ sở dữ liệu để phân tích sau này.


⚙️ Cách thức hoạt động
1. Camera Stream: Dữ liệu video được lấy từ camera thông qua URL stream và được xử lý bởi OpenCV để phát hiện khuôn mặt và mắt người lái xe.
2. Phát hiện mắt đóng: Nếu mắt người lái xe đóng liên tục trong hơn 2 giây, hệ thống sẽ kích hoạt cảnh báo.
3. Chụp ảnh và cảnh báo: Khi phát hiện tình trạng buồn ngủ, hệ thống sẽ chụp ảnh và phát âm thanh cảnh báo.
4. Giao diện web: Hệ thống cung cấp giao diện web (sử dụng Flask) để người dùng có thể theo dõi trạng thái trực tuyến.
  

📰 Poster

![image](https://github.com/user-attachments/assets/0d28a8a1-e0bd-4420-ae06-1bf4828374c1)



🤝 Đóng góp

Dự án được phát triển bởi 4 thành viên:

![image](https://github.com/user-attachments/assets/428bb98a-60ca-4143-a5af-f77995e84949)



© 2025 NHÓM 2, CNTT16-04, TRƯỜNG ĐẠI HỌC ĐẠI NAM
