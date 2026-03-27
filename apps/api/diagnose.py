#!/usr/bin/env python3
"""
Diagnostic script to check hand detection, model loading, and character prediction.
This will help identify WHERE the issue is.
"""
import sys
import os
sys.path.insert(0, '/z/HandTalk/apps/api')

import cv2
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("="*60)
print("HANDTALK DIAGNOSTICS")
print("="*60)

# Test 1: Check models exist
print("\n1. Checking model files...")
model_paths = [
    '/z/HandTalk/apps/api/cnn8grps_rad1_model.h5',
    '/z/HandTalk/apps/api/cnn8grps_rad1_isl_model.h5',
]
for path in model_paths:
    if os.path.exists(path):
        size_mb = os.path.getsize(path) / (1024*1024)
        print(f"   [OK] {os.path.basename(path)} ({size_mb:.1f} MB)")
    else:
        print(f"   [ERROR] {path} NOT FOUND")

# Test 2: Load model manager
print("\n2. Loading model manager...")
try:
    from src.services.model_manager import get_model_manager
    model_manager = get_model_manager()
    modes = model_manager.get_available_modes()
    print(f"   [OK] Model manager loaded")
    print(f"   Available models: {modes}")
except Exception as e:
    print(f"   [ERROR] Error loading model manager: {e}")
    sys.exit(1)

# Test 3: Check hand detector
print("\n3. Testing hand detector...")
try:
    from cvzone.HandTrackingModule import HandDetector
    hd = HandDetector(maxHands=1)
    print(f"   [OK] Hand detector initialized")
except Exception as e:
    print(f"   [ERROR] Error initializing hand detector: {e}")
    sys.exit(1)

# Test 4: Check camera access
print("\n4. Testing camera access...")
try:
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"   [OK] Camera works ({frame.shape[0]}x{frame.shape[1]})")
            cap.release()
        else:
            print(f"   [ERROR] Camera can't read frame")
    else:
        print(f"   [ERROR] Camera not available")
except Exception as e:
    print(f"   [ERROR] Error accessing camera: {e}")

# Test 5: Test hand detection with camera
print("\n5. Testing hand detection (point hand at camera)...")
print("   Waiting for hand... (press ESC to skip)")
cap = cv2.VideoCapture(0)
hand_found = False
for i in range(30):  # 30 frames
    ret, frame = cap.read()
    if not ret:
        print("   [ERROR] Camera frame failed")
        break

    hands, _ = hd.findHands(frame, draw=False, flipType=True)
    if hands:
        hand = hands[0]
        pts = hand.get("lmList")
        bbox = hand.get("bbox")
        if pts and len(pts) == 21:
            hand_found = True
            print(f"   [OK] Hand detected!")
            print(f"      Landmarks: 21 points")
            print(f"      BBox: {bbox}")
            break

    if i % 10 == 0:
        print(f"      Checking... frame {i}")

if not hand_found:
    print(f"   [WARN]  No hand detected in 30 frames")
    print(f"      Check: Lighting, hand distance (30-40cm), hand visibility")

cap.release()

# Test 6: Test character prediction
print("\n6. Testing character prediction...")
try:
    from main import _decode_group_to_char, predict_letter_from_skeleton_and_landmarks, draw_skeleton_from_landmarks

    # Create dummy skeleton
    pts = [[i*10, i*10] for i in range(21)]
    white = np.ones((400, 400, 3), np.uint8) * 255

    # Test decoder with group 2 (C, O)
    result = _decode_group_to_char(2, 0, pts)
    print(f"   [OK] Character decoder works")
    print(f"      Test: group 2 -> '{result}' (expected 'O')")

    # Test skeleton drawing
    skeleton = draw_skeleton_from_landmarks(pts, 200, 200)
    print(f"   [OK] Skeleton drawing works ({skeleton.shape})")

except Exception as e:
    print(f"   [ERROR] Error in prediction: {e}")
    import traceback
    traceback.print_exc()

# Test 7: Test model prediction
print("\n7. Testing model prediction...")
try:
    # Create dummy skeleton image
    skeleton = np.ones((400, 400, 3), np.uint8) * 255

    ch1, top1, margin, prob_dist = model_manager.predict(skeleton)
    print(f"   [OK] Model prediction works")
    print(f"      ch1={ch1}, top1={top1:.3f}, margin={margin:.3f}")
    print(f"      prob_dist shape: {prob_dist.shape}" if hasattr(prob_dist, 'shape') else f"      prob_dist: {type(prob_dist)}")

except Exception as e:
    print(f"   [ERROR] Error in model prediction: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("DIAGNOSTIC COMPLETE")
print("="*60)
print("\nIf all tests show [OK], the system should work!")
print("If hand detection shows [WARN], check lighting and hand distance")
print("If any test shows [ERROR], that's where the problem is")
