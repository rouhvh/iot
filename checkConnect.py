import cv2

# Thử mở luồng video
url = 'http://192.168.137.225:81/stream'
cap = cv2.VideoCapture(url)

if cap.isOpened():
    print("Kết nối thành công!")

    # Đọc FPS và kích thước frame
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"FPS: {fps}")
    print(f"Kích thước Frame: {width}x{height}")

    ret, frame = cap.read()
    if ret:
        print("Đã nhận frame đầu tiên.")
        cv2.imshow("Test Frame", frame)
        cv2.waitKey(5000)  # Hiển thị trong 5 giây
        cv2.destroyAllWindows()
    else:
        print("Không nhận được frame nào.")
else:
    print("Kết nối thất bại!")
    # In ra lỗi chi tiết
    print(f"Error code: {cap.get(cv2.CAP_PROP_POS_MSEC)}")

cap.release()
