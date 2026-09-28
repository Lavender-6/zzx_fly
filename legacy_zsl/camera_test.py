import cv2

# 改成 video11 再试一次
cap = cv2.VideoCapture('/dev/video11')

ret, frame = cap.read()
if ret:
    print("✅ 读取成功！")
    cv2.imwrite("test.jpg", frame)
else:
    print("❌ 读取失败")

cap.release()
