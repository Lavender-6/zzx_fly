import cv2

# 就是这个！/dev/video0
cap = cv2.VideoCapture(0)

if cap.isOpened():
    print("✅ 摄像头打开成功！！！")
    ret, frame = cap.read()
    if ret:
        cv2.imwrite("test.jpg", frame)
        print("✅ 照片已保存：test.jpg")
else:
    print("❌ 打不开")

cap.release()
