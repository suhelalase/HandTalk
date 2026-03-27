#!/usr/bin/env python3
"""
Stable hand detection with Kalman filtering and smoothing
"""
import cv2
import mediapipe as mp
import numpy as np
import sys
from collections import deque

# Kalman filter for smoothing
class KalmanTracker:
    def __init__(self):
        self.kf = cv2.KalmanFilter(4, 2)
        self.kf.measurementMatrix = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ], dtype=np.float32)

        self.kf.transitionMatrix = np.array([
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)

        self.kf.processNoiseCov = np.eye(4, dtype=np.float32) * 0.01
        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 0.1

    def predict(self, x, y):
        measurement = np.array([[x], [y]], dtype=np.float32)
        self.kf.correct(measurement)
        prediction = self.kf.predict()
        return prediction[0][0], prediction[1][0]

# MediaPipe setup with HIGHER thresholds for stability
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,  # HIGHER - more stable
    min_tracking_confidence=0.7     # HIGHER - maintains tracking
)

# Camera setup
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
cap.set(cv2.CAP_PROP_BRIGHTNESS, 100)
cap.set(cv2.CAP_PROP_CONTRAST, 80)

print("[OK] Camera with STABILIZATION mode")
print("[TIPS] Keep hand visible and STEADY")
print("[KEYS] Q=quit, S=save, L=increase light, D=decrease light")

frame_count = 0
hand_detected = 0
trackers = {}  # One kalman filter per landmark

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    frame = cv2.flip(frame, 1)
    h, w, c = frame.shape

    # Enhance brightness
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge([l, a, b])
    frame_enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    frame_rgb = cv2.cvtColor(frame_enhanced, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    display = frame.copy()

    # Draw info
    cv2.rectangle(display, (0, 0), (600, 150), (20, 20, 20), -1)
    cv2.putText(display, f"Frame: {frame_count} | Detection: {hand_detected}/{frame_count} ({100*hand_detected/max(1,frame_count):.1f}%)",
                (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(display, "STABILIZATION ACTIVE - Keep hand steady", (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 200, 0), 2)

    if results.multi_hand_landmarks:
        hand_detected += 1

        for hand_idx, (hand_landmarks, handedness) in enumerate(zip(results.multi_hand_landmarks, results.multi_handedness)):
            # Initialize trackers for this hand if needed
            hand_id = f"hand_{hand_idx}"
            if hand_id not in trackers:
                trackers[hand_id] = {}
                for i in range(21):
                    trackers[hand_id][i] = KalmanTracker()

            # Draw hand with smoothing
            smoothed_landmarks = []
            confidence_sum = 0

            for idx, lm in enumerate(hand_landmarks.landmark):
                pixel_x = int(lm.x * w)
                pixel_y = int(lm.y * h)

                # Apply Kalman smoothing
                smoothed_x, smoothed_y = trackers[hand_id][idx].predict(pixel_x, pixel_y)
                smoothed_landmarks.append([smoothed_x, smoothed_y])
                confidence_sum += lm.z

                # Draw smoothed point
                color = (0, 255, 0) if idx in [0, 5, 9, 13, 17] else (100, 200, 100)
                cv2.circle(display, (int(smoothed_x), int(smoothed_y)), 4, color, -1)

            # Draw connections
            connections = [
                (0, 1), (1, 2), (2, 3), (3, 4),      # Thumb
                (0, 5), (5, 6), (6, 7), (7, 8),      # Index
                (0, 9), (9, 10), (10, 11), (11, 12), # Middle
                (0, 13), (13, 14), (14, 15), (15, 16), # Ring
                (0, 17), (17, 18), (18, 19), (19, 20), # Pinky
                (5, 9), (9, 13), (13, 17)             # Palm
            ]

            for start, end in connections:
                start_pt = tuple(map(int, smoothed_landmarks[start]))
                end_pt = tuple(map(int, smoothed_landmarks[end]))
                cv2.line(display, start_pt, end_pt, (255, 0, 0), 2)

            # Draw confidence indicator
            avg_conf = confidence_sum / 21
            conf_color = (0, 255, 0) if avg_conf > 0.7 else (0, 165, 255)
            cv2.putText(display, f"Hand {hand_idx+1} | Confidence: {avg_conf:.2f} | {handedness.classification[0].label}",
                        (10, 130 + hand_idx * 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, conf_color, 2)

            if frame_count % 60 == 0:
                print(f"[OK] Hand tracking: confidence={avg_conf:.3f}")

    cv2.imshow("HandTalk - Stable Detection", display)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        cv2.imwrite(f"stable_{frame_count}.jpg", display)
        print(f"[SAVE] stable_{frame_count}.jpg")
    elif key == ord('l'):
        cap.set(cv2.CAP_PROP_BRIGHTNESS, min(200, cap.get(cv2.CAP_PROP_BRIGHTNESS) + 20))
        print(f"[ADJUST] Brightness increased")
    elif key == ord('d'):
        cap.set(cv2.CAP_PROP_BRIGHTNESS, max(0, cap.get(cv2.CAP_PROP_BRIGHTNESS) - 20))
        print(f"[ADJUST] Brightness decreased")

cap.release()
cv2.destroyAllWindows()
hands.close()

print(f"\n[RESULT] Detection rate: {100*hand_detected/max(1,frame_count):.1f}%")
