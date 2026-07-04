import sys
import logging
import cv2
import os

# Menghindari konflik Qt plugin antara PyQt5 dan OpenCV
if "QT_QPA_PLATFORM_PLUGIN_PATH" in os.environ:
    os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH")

import mediapipe as mp
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QGridLayout
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from pymodbus.client import ModbusTcpClient

# Konfigurasi MediaPipe
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    hand_gesture_signal = pyqtSignal(list, bool)

    def __init__(self):
        super().__init__()
        self._run_flag = True

    def run(self):
        cap = cv2.VideoCapture(0)
        with mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7) as hands:
            while self._run_flag:
                ret, frame = cap.read()
                if ret:
                    # BGR ke RGB untuk MediaPipe
                    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = hands.process(image_rgb)
                    
                    hand_detected = False
                    finger_states = [False, False, False, False]
                    
                    if results.multi_hand_landmarks:
                        hand_detected = True
                        for hand_landmarks in results.multi_hand_landmarks:
                            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                            
                            # Deteksi state jari berdasarkan koordinat Y
                            # (Nilai Y lebih kecil berarti jari mengarah ke atas/diangkat)
                            # Index (Telunjuk)
                            finger_states[0] = hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y
                            # Middle (Tengah)
                            finger_states[1] = hand_landmarks.landmark[12].y < hand_landmarks.landmark[10].y
                            # Ring (Manis)
                            finger_states[2] = hand_landmarks.landmark[16].y < hand_landmarks.landmark[14].y
                            # Pinky (Kelingking)
                            finger_states[3] = hand_landmarks.landmark[20].y < hand_landmarks.landmark[18].y
                            
                    self.hand_gesture_signal.emit(finger_states, hand_detected)
                    self.change_pixmap_signal.emit(frame)
        cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()


class ModbusApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modbus TCP PLC Client with AI Gesture")
        self.resize(700, 900)
        
        self.plc_ip = "192.168.1.50"
        
        # Initialize Modbus TCP Client
        self.client = ModbusTcpClient(self.plc_ip)
        
        # Menyimpan status tangan terakhir agar tidak mengirim Modbus berkali-kali
        self.last_finger_states = [False, False, False, False]
        
        self.initUI()
        
        # Mulai Thread Kamera
        self.thread = VideoThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.hand_gesture_signal.connect(self.update_gesture)
        self.thread.start()
        
        # Timer for polling M100-M103
        self.timer = QTimer()
        self.timer.timeout.connect(self.poll_data)
        self.timer.start(1000) # Poll every 1 second
        
    def initUI(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        
        # Kamera View
        main_layout.addWidget(QLabel("<b>Webcam Hand Tracking:</b>"))
        self.video_label = QLabel()
        self.video_label.setFixedSize(640, 480)
        self.video_label.setStyleSheet("background-color: black;")
        main_layout.addWidget(self.video_label, alignment=Qt.AlignCenter)
        
        main_layout.addSpacing(10)
        
        # Top section for LEDs (M100-M103)
        read_layout = QGridLayout()
        main_layout.addWidget(QLabel("<b>Read Data (M100 - M103)</b>"))
        main_layout.addLayout(read_layout)
        
        self.leds = []
        for i in range(4):
            lbl = QLabel(f"M10{i}")
            led = QLabel()
            led.setFixedSize(30, 30)
            led.setStyleSheet("background-color: gray; border-radius: 15px;")
            self.leds.append(led)
            read_layout.addWidget(lbl, 0, i, alignment=Qt.AlignCenter)
            read_layout.addWidget(led, 1, i, alignment=Qt.AlignCenter)
            
        main_layout.addSpacing(20)
            
        # Middle section for Switches (M200-M203)
        write_layout = QGridLayout()
        main_layout.addWidget(QLabel("<b>Write Data (M200 - M203) - Manual / Gesture</b>"))
        main_layout.addLayout(write_layout)
        
        self.switches = []
        for i in range(4):
            btn = QPushButton(f"M20{i} OFF")
            btn.setCheckable(True)
            btn.setStyleSheet("background-color: lightgray;")
            btn.clicked.connect(lambda checked, idx=i: self.toggle_switch(idx, checked))
            self.switches.append(btn)
            write_layout.addWidget(btn, 0, i)
            
        main_layout.addSpacing(20)
            
        # Bottom section for Console Log
        main_layout.addWidget(QLabel("<b>Console Log:</b>"))
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("background-color: black; color: lime;")
        main_layout.addWidget(self.console)
        
    def update_image(self, cv_img):
        qt_img = self.convert_cv_qt(cv_img)
        self.video_label.setPixmap(qt_img)
    
    def convert_cv_qt(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    def update_gesture(self, finger_states, hand_detected):
        # Jika tidak ada tangan terdeteksi, bebaskan kontrol manual (jangan di-overwrite)
        if not hand_detected:
            return
            
        for i in range(4):
            if self.last_finger_states[i] != finger_states[i]:
                self.last_finger_states[i] = finger_states[i]
                
                # Update tombol di GUI dan kirim ke Modbus
                self.switches[i].setChecked(finger_states[i])
                self.toggle_switch(i, finger_states[i])

    def log_msg(self, msg):
        self.console.append(msg)
        print(msg) # Print to terminal as well
        
    def toggle_switch(self, idx, checked):
        address = 200 + idx
        try:
            if not self.client.connected:
                self.client.connect()
            result = self.client.write_coil(address, checked)
            if result.isError():
                self.log_msg(f"Error writing to M{address}")
            else:
                state = "ON" if checked else "OFF"
                if checked:
                    self.switches[idx].setText(f"M{address} ON")
                    self.switches[idx].setStyleSheet("background-color: lightgreen;")
                else:
                    self.switches[idx].setText(f"M{address} OFF")
                    self.switches[idx].setStyleSheet("background-color: lightgray;")
                self.log_msg(f"Wrote {state} to M{address}")
        except Exception as e:
            self.log_msg(f"Exception writing to M{address}: {e}")
            
    def poll_data(self):
        try:
            if not self.client.connected:
                if self.client.connect():
                    self.log_msg(f"Connected to PLC at {self.plc_ip}")
                else:
                    self.log_msg(f"Failed to connect to PLC at {self.plc_ip}")
                    return
                    
            # Read M100 - M103
            result = self.client.read_coils(100, count=4)
            if result.isError():
                self.log_msg("Error reading M100-M103")
            else:
                bits = result.bits
                # self.log_msg(f"Read M100-M103: {bits[:4]}") # Dihapus agar tidak terlalu memenuhi konsol tiap detik
                for i in range(4):
                    if bits[i]:
                        self.leds[i].setStyleSheet("background-color: red; border-radius: 15px;")
                    else:
                        self.leds[i].setStyleSheet("background-color: gray; border-radius: 15px;")
        except Exception as e:
            self.log_msg(f"Exception polling data: {e}")

    def closeEvent(self, event):
        self.thread.stop()
        if self.client.connected:
            self.client.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModbusApp()
    window.show()
    sys.exit(app.exec_())
