#!/usr/bin/env python3
"""
Enhanced hand detection with diagnostics and auto-improvements
"""
import cv2
import mediapipe as mp
import numpy as np
import sys

# MediaPipe setup
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Open camera with settings optimization
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("[ERROR] Cannot open camera")
    sys.exit(1)

# Optimize camera settings for better detection
print("[INFO] Optimizing camera settings...")
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, -13)  # Enable auto exposure
cap.set(cv2.CAP_PROP_BRIGHTNESS, 80)
cap.set(cv2.CAP_PROP_CONTRAST, 70)
cap.set(cv2.CAP_PROP_SATURATION, 50)
cap.set(cv2.CAP_PROP_GAIN, 70)

print("[OK] Camera opened")
print("[USAGE] Move hand into frame, show clear hand gestures")
print("[KEYS] Q=quit, S=screenshot, B=brightness+, V=brightness-, C=contrast+, X=contrast-")

# Start with lower thresholds for detection
min_detection_conf = 0.4  # Lower threshold
min_tracking_conf = 0.3

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=min_detection_conf,
    min_tracking_confidence=min_tracking_conf
)

frame_count = 0
hand_detected_count = 0
brightness_offset = 0
contrast_offset = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Cannot read frame from camera")
        break

    frame_count += 1

    # Flip for selfie view
    frame = cv2.flip(frame, 1)
    h, w, c = frame.shape

    # Apply brightness/contrast adjustments
    if brightness_offset != 0 or contrast_offset != 0:
        frame = np.clip(frame.astype(np.float32) + brightness_offset, 0, 255).astype(np.uint8)
        if contrast_offset != 0:
            frame = cv2.convertScaleAbs(frame, alpha=1 + contrast_offset/100, beta=0)

    # Enhance image quality with CLAHE (Contrast Limited Adaptive Histogram Equalization)
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge([l, a, b])
    frame_enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    # Calculate image brightness
    gray = cv2.cvtColor(frame_enhanced, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)

    # Convert to RGB for MediaPipe
    frame_rgb = cv2.cvtColor(frame_enhanced, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    # Create display frame
    display = frame.copy()

    # Draw info panel
    cv2.rectangle(display, (0, 0), (500, 220), (20, 20, 20), -1)
    cv2.putText(display, f"Frame: {frame_count}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(display, f"Detection Conf: {min_detection_conf:.2f}", (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 1)
    cv2.putText(display, f"Brightness: {brightness:.0f}/255", (10, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 1)

    # Brightness indicator
    brightness_color = (0, 255, 0) if 80 < brightness < 200 else (0, 0, 255)
    cv2.putText(display, f"Lighting: {'GOOD' if 80 < brightness < 200 else 'BAD (dark)' if brightness < 80 else 'BAD (too bright)'}",
                (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, brightness_color, 2)

    det_rate = (hand_detected_count / frame_count * 100) if frame_count > 0 else 0
    cv2.putText(display, f"Detection Rate: {det_rate:.1f}%", (10, 190),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)

    # Draw detection results
    if results.multi_hand_landmarks:
        hand_detected_count += 1
        cv2.putText(display, f"HANDS FOUND: {len(results.multi_hand_landmarks)}", (10, 250),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

        for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            # Draw landmarks
            mp_drawing.draw_landmarks(
                display,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=3, circle_radius=3),
                mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=3)
            )

            # Print first hand details
            if hand_idx == 0:
                print(f"\n[OK] Hand detected! Frame {frame_count}")
                for idx in [0, 4, 8, 12, 16, 20]:
                    lm = hand_landmarks.landmark[idx]
                    print(f"  Point {idx}: x={lm.x:.3f}, y={lm.y:.3f}, z={lm.z:.3f}, conf={lm.z:.3f}")
    else:
        if frame_count % 30 == 0:  # Print every 30 frames to avoid spam
            print(f"[WAIT] Waiting for hand... (frame {frame_count})")
        cv2.putText(display, "NO HAND - MOVE HAND INTO FRAME", (10, 250),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # Draw brightness bar
    bar_width = int((brightness / 255) * 200)
    cv2.rectangle(display, (550, 30), (750, 50), (100, 100, 100), -1)
    cv2.rectangle(display, (550, 30), (550 + bar_width, 50), brightness_color, -1)
    cv2.putText(display, "Light Level", (550, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

    # Display frame
    cv2.imshow("HandTalk - Hand Detection (Enhanced)", display)

    # Handle keys
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == ord('Q'):
        print("[OK] Quit")
        break
    elif key == ord('s') or key == ord('S'):
        filename = f"hand_debug_{frame_count}.jpg"
        cv2.imwrite(filename, display)
        print(f"[SAVE] Screenshot: {filename}")
    elif key == ord('b') or key == ord('B'):
        brightness_offset += 20
        print(f"[ADJUST] Brightness +20 (total: {brightness_offset})")
    elif key == ord('v') or key == ord('V'):
        brightness_offset -= 20
        print(f"[ADJUST] Brightness -20 (total: {brightness_offset})")
    elif key == ord('c') or key == ord('C'):
        contrast_offset += 10
        print(f"[ADJUST] Contrast +10 (total: {contrast_offset})")
    elif key == ord('x') or key == ord('X'):
        contrast_offset -= 10
        print(f"[ADJUST] Contrast -10 (total: {contrast_offset})")
    elif key == ord('d') or key == ord('D'):
        min_detection_conf = max(0.1, min_detection_conf - 0.1)
        hands.close()
        hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=min_detection_conf,
            min_tracking_confidence=min_detection_conf - 0.1
        )
        print(f"[ADJUST] Detection threshold lowered to {min_detection_conf:.2f}")

cap.release()
cv2.destroyAllWindows()
hands.close()

print("\n" + "="*60)
print("DIAGNOSTIC SUMMARY")
print("="*60)
print(f"Total frames: {frame_count}")
print(f"Frames with hand: {hand_detected_count}")
print(f"Detection rate: {hand_detected_count/frame_count*100:.1f}%")
if hand_detected_count == 0:
    print("\n[RECOMMENDATION] No hands detected!")
    print("  1. Check LIGHTING - move to bright area")
    print("  2. Check DISTANCE - keep hand 30-40cm from camera")
    print("  3. Check VISIBILITY - full hand in frame")
    print("  4. Try again with: 'B' for brightness, 'D' to lower detection threshold")
else:
    print(f"\n[SUCCESS] Hand detection working!")
