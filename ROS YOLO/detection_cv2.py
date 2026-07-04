from ultralytics import YOLO
import cv2

# Load model YOLOv8 (pretrained COCO)
model = YOLO("best.pt")  # versi ringan (nano)

# Buka webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Deteksi objek
    results = model(frame)

    # Visualisasi hasil
    annotated_frame = results[0].plot()

    # Tampilkan hasil
    cv2.imshow("Deteksi Objek YOLOv8", annotated_frame)

    # Tekan Q untuk keluar
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()