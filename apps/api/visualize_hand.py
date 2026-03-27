#!/usr/bin/env python3
"""
Real-time hand detection visualization
Shows camera feed with MediaPipe hand landmarks overlay
"""
import cv2
import mediapipe as mp
import numpy as np
import sys

# MediaPipe setup
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Open camera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("[ERROR] Cannot open camera")
    sys.exit(1)

print("[OK] Camera opened")
print("Press 'Q' to quit, 'S' to save screenshot")

frame_count = 0
hand_detected_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Cannot read frame from camera")
        break

    frame_count += 1

    # Flip for selfie view
    frame = cv2.flip(frame, 1)
    h, w, c = frame.shape

    # Convert to RGB for MediaPipe
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    # Draw FPS and hand status
    cv2.putText(frame, f"Frame: {frame_count}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    if results.multi_hand_landmarks:
        hand_detected_count += 1
        cv2.putText(frame, f"HANDS DETECTED: {len(results.multi_hand_landmarks)}", (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Draw landmarks for each hand
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
            )

            # Print landmark coordinates
            print(f"\n=== Hand {len(results.multi_hand_landmarks)} Landmarks ===")
            for idx, lm in enumerate(hand_landmarks.landmark):
                print(f"  {idx}: x={lm.x:.3f}, y={lm.y:.3f}, z={lm.z:.3f}")
    else:
        cv2.putText(frame, "NO HAND DETECTED", (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # Draw detection status
    det_rate = (hand_detected_count / frame_count * 100) if frame_count > 0 else 0
    cv2.putText(frame, f"Detection Rate: {det_rate:.1f}%", (10, 130),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    # Display frame
    cv2.imshow("HandTalk - Hand Detection Visualization", frame)

    # Handle keys
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == ord('Q'):
        print("[OK] Quit requested")
        break
    elif key == ord('s') or key == ord('S'):
        filename = f"hand_detection_{frame_count}.jpg"
        cv2.imwrite(filename, frame)
        print(f"[OK] Screenshot saved: {filename}")

cap.release()
cv2.destroyAllWindows()
hands.close()

print("\n" + "="*50)
print("VISUALIZATION SUMMARY")
print("="*50)
print(f"Total frames: {frame_count}")
print(f"Hands detected: {hand_detected_count}")
print(f"Detection rate: {hand_detected_count/frame_count*100:.1f}%")
