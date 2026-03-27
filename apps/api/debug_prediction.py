#!/usr/bin/env python3
"""
Debug character prediction - see exactly what the model predicts vs what decoder returns
"""
import cv2
import mediapipe as mp
import numpy as np
import sys
from pathlib import Path

# Add api to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.model_manager import ModelManager

# Initialize
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

model_mgr = ModelManager()
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_BRIGHTNESS, 100)

print("[OK] Debug mode active")
print("[KEYS] Q=quit, C=capture and predict")

frame_count = 0
white = np.ones((400, 400, 3), dtype=np.uint8) * 255

def draw_skeleton_simple(landmarks, w, h):
    """Simple skeleton drawing"""
    os_offset = ((400 - w) // 2) - 15
    os1_offset = ((400 - h) // 2) - 15
    canvas = np.copy(white)

    lms_offset = np.array([[p[0] + os_offset, p[1] + os1_offset] for p in landmarks], dtype=np.int32)

    for start in [0, 5, 9, 13, 17]:
        for i in range(start, min(start + 3, 20)):
            cv2.line(canvas, tuple(lms_offset[i]), tuple(lms_offset[i + 1]), (0, 255, 0), 2)

    for start, end in [(5, 9), (9, 13), (13, 17), (0, 5), (0, 17)]:
        cv2.line(canvas, tuple(lms_offset[start]), tuple(lms_offset[end]), (0, 255, 0), 2)

    for point in lms_offset:
        cv2.circle(canvas, tuple(point), 2, (0, 0, 255), 1)

    return canvas

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    frame = cv2.flip(frame, 1)
    h, w, c = frame.shape

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    display = frame.copy()

    if results.multi_hand_landmarks:
        hand_lms = results.multi_hand_landmarks[0]

        # Extract landmark positions
        pts = np.array([[lm.x * w, lm.y * h] for lm in hand_lms.landmark], dtype=np.float32)

        # Draw skeleton
        skeleton = draw_skeleton_simple(pts, w, h)

        # Display info
        cv2.putText(display, "HAND DETECTED - Press C to predict", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(display, f"Frame: {frame_count}", (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

        # On 'C' key, make prediction
        key = cv2.waitKey(1) & 0xFF
        if key == ord('c') or key == ord('C'):
            print("\n" + "="*70)
            print(f"PREDICTION DEBUG - Frame {frame_count}")
            print("="*70)

            # Get model prediction
            ch1, top1, margin, prob_dist = model_mgr.predict(skeleton, mode="ASL")

            print(f"\nMODEL OUTPUT (RAW):")
            print(f"  ch1 (top prediction): {ch1}")
            print(f"  top1 confidence: {top1:.4f}")
            print(f"  margin (top-2nd): {margin:.4f}")
            print(f"  probability distribution: {prob_dist}")
            print(f"  argmax indices: {np.argsort(prob_dist)[::-1][:3]}")

            # Get 2nd best prediction
            prob2 = prob_dist.copy()
            prob2[ch1] = -1.0
            ch2 = int(np.argmax(prob2))

            print(f"\nCH2 EXTRACTION:")
            print(f"  ch2 (2nd best): {ch2}")
            print(f"  top2 confidence: {prob2[ch2]:.4f}")

            print(f"\nPAIR: [{ch1}, {ch2}]")

            # Check decoder groups
            aemnst_pairs = [[5, 2], [5, 3], [3, 5], [3, 6], [3, 0], [3, 2], [6, 4], [6, 1], [6, 2], [6, 6], [6, 7], [6, 0], [6, 5],
                            [4, 1], [1, 0], [1, 1], [6, 3], [1, 6], [5, 6], [5, 1], [4, 5], [1, 4], [1, 5], [2, 0], [2, 6], [4, 6],
                            [1, 0], [5, 7], [1, 6], [6, 1], [7, 6], [2, 5], [7, 1], [5, 4], [7, 0], [7, 5], [7, 2]]

            print(f"\nDECODER CHECK:")
            print(f"  Is pair in AEMNST? {[ch1, ch2] in aemnst_pairs}")

            # Check key landmark conditions
            print(f"\nLANDMARK POSITIONS (sample):")
            print(f"  pts[0] (wrist): ({pts[0][0]:.1f}, {pts[0][1]:.1f})")
            print(f"  pts[4] (thumb): ({pts[4][0]:.1f}, {pts[4][1]:.1f})")
            print(f"  pts[6] (index): ({pts[6][0]:.1f}, {pts[6][1]:.1f})")
            print(f"  pts[8] (index tip): ({pts[8][0]:.1f}, {pts[8][1]:.1f})")
            print(f"  pts[20] (pinky tip): ({pts[20][0]:.1f}, {pts[20][1]:.1f})")

            # Call actual decoder
            from main import _decode_group_to_char
            pred_char = _decode_group_to_char(ch1, ch2, pts)

            print(f"\nFINAL PREDICTION: '{pred_char}'")
            print("="*70)
    else:
        cv2.putText(display, "NO HAND - Move into frame", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break

    cv2.imshow("DEBUG - Character Prediction", display)

cap.release()
cv2.destroyAllWindows()
