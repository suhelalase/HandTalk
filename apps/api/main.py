import asyncio
import base64
import io
import json
import logging
import math
import os
import sys
import time
from collections import Counter, deque
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from cvzone.HandTrackingModule import HandDetector

# Add project root for imports
sys.path.append(str(Path(__file__).resolve().parents[2]))
# If you have a shared utils package, you can import here

from apps.api.src.services import get_model_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize model manager (loads ASL model)
model_manager = get_model_manager()

# Hand detector
hd = HandDetector(maxHands=1, detectionCon=0.75, minTrackCon=0.75)

# White background for skeleton
white = np.ones((400, 400, 3), np.uint8) * 255

app = FastAPI(title="HandTalk Inference API", version="1.0.0")

# Simple in-memory session store
sessions = {}

def distance(x, y):
    return math.sqrt(((x[0] - y[0]) ** 2) + ((x[1] - y[1]) ** 2))

def _decode_group_to_char(ch1: int, ch2: int, pts, pts2=None) -> str:
    """
    Character decoder using EXACT (ch1, ch2) pair matching from legacy code.
    This is the proven working logic!
    """
    try:
        if pts is None or len(pts) < 21:
            return "?"

        pair = [ch1, ch2]

        # Pre-calculate distances once
        d_thumb_idx = ((pts[4][0]-pts[11][0])**2 + (pts[4][1]-pts[11][1])**2)**0.5
        d_idx_ring = ((pts[8][0]-pts[16][0])**2 + (pts[8][1]-pts[16][1])**2)**0.5

        # Default character map for each group
        defaults = {0: 'S', 1: 'B', 2: 'O', 3: 'H', 4: 'L', 5: 'P', 6: 'X', 7: 'J'}

        # AEMNST pairs - check if pair matches, then apply landmark rule
        aemnst_pairs = [[5, 2], [5, 3], [3, 5], [3, 6], [3, 0], [3, 2], [6, 4], [6, 1], [6, 2], [6, 6], [6, 7], [6, 0], [6, 5],
                        [4, 1], [1, 0], [1, 1], [6, 3], [1, 6], [5, 6], [5, 1], [4, 5], [1, 4], [1, 5], [2, 0], [2, 6], [4, 6],
                        [1, 0], [5, 7], [1, 6], [6, 1], [7, 6], [2, 5], [7, 1], [5, 4], [7, 0], [7, 5], [7, 2]]
        if pair in aemnst_pairs:
            if (pts[6][1] < pts[8][1] and pts[10][1] < pts[12][1] and pts[14][1] < pts[16][1] and pts[18][1] < pts[20][1]):
                return 'A'

        # [C, O] with index-ring distance
        if pair in [[2, 2], [2, 1]]:
            if pts[5][0] < pts[4][0]:
                return 'C'

        # M from AEMNST pairs
        if pair in [[0, 0], [0, 6], [0, 2], [0, 5], [0, 1], [0, 7], [5, 2], [7, 6], [7, 1]]:
            if (pts[0][0] > pts[8][0] and pts[0][0] > pts[4][0] and pts[0][0] > pts[12][0] and pts[0][0] > pts[16][0] and pts[0][0] > pts[20][0]) and pts[5][0] > pts[4][0]:
                return 'M'

        # C with index-ring distance
        if pair in [[6, 0], [6, 6], [6, 2]]:
            if d_idx_ring < 52:
                return 'C'

        # G from group matching
        if pair in [[1, 4], [1, 5], [1, 6], [1, 3], [1, 0]]:
            if pts[6][1] > pts[8][1] and pts[14][1] < pts[16][1] and pts[18][1] < pts[20][1] and pts[0][0] < pts[8][0] and pts[0][0] < pts[12][0] and pts[0][0] < pts[16][0] and pts[0][0] < pts[20][0]:
                return 'G'

        # L from group matching
        if pair in [[4, 6], [4, 1], [4, 5], [4, 3], [4, 7]]:
            if pts[4][0] > pts[0][0]:
                return 'L'

        # G continued
        if pair in [[5, 3], [5, 0], [5, 7], [5, 4], [5, 2], [5, 1], [5, 5]]:
            if pts[2][1] + 15 < pts[16][1]:
                return 'G'

        # X from group matching
        if pair in [[6, 4], [6, 1], [6, 2]]:
            if d_thumb_idx > 55:
                return 'X'

        # L continued
        if pair in [[1, 4], [1, 6], [1, 1]]:
            if (d_thumb_idx > 50) and (pts[6][1] > pts[8][1] and pts[10][1] < pts[12][1] and pts[14][1] < pts[16][1] and pts[18][1] < pts[20][1]):
                return 'L'

        # L continued
        if pair in [[3, 6], [3, 4]]:
            if pts[4][0] < pts[0][0]:
                return 'L'

        # L continued
        if pair in [[2, 2], [2, 5], [2, 4]]:
            if pts[1][0] < pts[12][0]:
                return 'L'

        # Return default for the group
        return defaults.get(ch1, '?')

    except Exception as e:
        logger.error(f"Error in character decoding: {e}")
        return '?'


def predict_letter_from_skeleton_and_landmarks(skeleton_img, pts, pts2=None, mode: str = "ASL"):
    """Predict ASL letter from skeleton image + landmark disambiguation rules."""
    try:
        # Validate inputs
        if skeleton_img is None or pts is None:
            logger.warning("Invalid input: skeleton_img or pts is None")
            return "?", 0.0, 0.0

        # Model predicts 8 gesture groups; we decode group -> specific letter via landmarks.
        model_result = model_manager.predict(skeleton_img, mode=mode)

        # Handle unpacking
        if not model_result or len(model_result) != 4:
            logger.error(f"Unexpected model output: {model_result}")
            return "?", 0.0, 0.0

        ch1, top1, margin, prob_dist = model_result

        if ch1 is None or ch1 < 0:
            return "?", 0.0, 0.0

        # Validate model output
        if prob_dist is None or len(prob_dist) != 8:
            logger.warning(f"Invalid probability distribution: {prob_dist}")
            return "?", 0.0, 0.0

        # Extract ch2 for disambiguation
        try:
            prob_copy = prob_dist.copy() if hasattr(prob_dist, 'copy') else np.array(prob_dist)
            prob_copy[ch1] = -1.0
            ch2 = int(np.argmax(prob_copy, axis=0))
        except Exception as e:
            logger.error(f"Error extracting ch2: {e}")
            ch2 = 0

        # Decode character
        ch = _decode_group_to_char(ch1, ch2, pts, pts2)

        if ch is None:
            return "?", 0.0, 0.0

        # Space condition (ported; produces a space when pinky is down but others match)
        if ch in ("B", "E", "S", "X", "Y"):
            if pts[6][1] > pts[8][1] and pts[10][1] < pts[12][1] and pts[14][1] < pts[16][1] and pts[18][1] > pts[20][1]:
                return " ", top1, margin

        return ch, top1, margin
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        return "?", 0.0, 0.0


def draw_skeleton_from_landmarks(landmarks, w, h):
    """Draw hand skeleton on white background - optimized for speed"""
    os_offset = ((400 - w) // 2) - 15
    os1_offset = ((400 - h) // 2) - 15
    canvas = np.copy(white)

    # Pre-calculate offsets for landmarks
    lms_offset = np.array([[p[0] + os_offset, p[1] + os1_offset] for p in landmarks], dtype=np.int32)

    # Draw fingers
    for start in [0, 5, 9, 13, 17]:
        for i in range(start, min(start + 3, 20)):  # Fixed: max i is 19, so i+1 is 20 (valid)
            cv2.line(canvas, tuple(lms_offset[i]), tuple(lms_offset[i + 1]), (0, 255, 0), 2)

    # Connect palm
    palm_pairs = [(5, 9), (9, 13), (13, 17), (0, 5), (0, 17)]
    for start, end in palm_pairs:
        cv2.line(canvas, tuple(lms_offset[start]), tuple(lms_offset[end]), (0, 255, 0), 2)

    # Draw landmark circles
    for point in lms_offset:
        cv2.circle(canvas, tuple(point), 2, (0, 0, 255), 1)

    return canvas


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = id(websocket)
    logger.info(f"WebSocket connected: {session_id}")
    sessions[session_id] = {
        "transcript": "",
        "stable_char": "",
        "stable_count": 0,
        "no_hand_count": 0,
        "last_committed": "",
        "pred_window": deque(maxlen=5),
    }
    try:
        while True:
            # Expect JSON: { image: base64-jpeg, inputMode: "letters"|"words" }
            data = await websocket.receive_text()
            payload = json.loads(data)
            b64 = payload.get("image", "")
            input_mode = payload.get("inputMode", "letters")
            frame_id = payload.get("frameId")
            client_ts = payload.get("clientTs")
            if not b64:
                continue

            t0 = time.perf_counter()
            # Decode image
            header, encoded = b64.split(",", 1)
            img_bytes = base64.b64decode(encoded)
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                continue
            t_decode = time.perf_counter()
            # Keep frame unflipped; frontend handles mirroring for display.
            hands, _ = hd.findHands(frame, draw=False, flipType=True)
            t_detect = time.perf_counter()
            current_char = ""
            sess = sessions[session_id]
            pred_ran = False
            if hands:
                try:
                    fh, fw = frame.shape[:2]
                    bx, by, bw, bh = hands[0].get("bbox", (0, 0, 0, 0))
                    if bw <= 0 or bh <= 0:
                        hands = []
                    else:
                        area = float(bw * bh)
                        frame_area = float(fw * fh)
                        if bw < 40 or bh < 40 or area < frame_area * 0.01 or area > frame_area * 0.90:
                            hands = []
                except Exception:
                    hands = []

            t_pred0 = t_detect
            t_pred1 = t_detect

            overlay = {"bbox": None, "landmarks": []}
            if hands:
                try:
                    overlay = {"bbox": hands[0].get("bbox"), "landmarks": hands[0].get("lmList", [])}
                except Exception:
                    overlay = {"bbox": None, "landmarks": []}

            if not hands:
                sess["no_hand_count"] += 1
                if sess["no_hand_count"] >= 2:
                    if input_mode == "words":
                        if sess["transcript"] and not sess["transcript"].endswith(" "):
                            sess["transcript"] += " "
                    sess["stable_char"] = ""
                    sess["stable_count"] = 0
                    sess["pred_window"].clear()
                t_end = time.perf_counter()
                await websocket.send_json(
                    {
                        "frameId": frame_id,
                        "clientTs": client_ts,
                        "timingMs": {
                            "decode": (t_decode - t0) * 1000.0,
                            "detect": (t_detect - t_decode) * 1000.0,
                            "predict": 0.0,
                            "total": (t_end - t0) * 1000.0,
                        },
                        "currentChar": "",
                        "transcript": sess["transcript"],
                        "inputMode": input_mode,
                        "modelAvailable": bool(getattr(model_manager, "is_model_available", lambda *_: False)("ASL")),
                        "overlay": overlay,
                    }
                )
                continue

            sess["no_hand_count"] = 0

            if hands:
                hand0 = hands[0]
                x, y, w, h = hand0["bbox"]
                pts = hand0.get("lmList")

                if pts and isinstance(pts, list) and len(pts) == 21:
                    skeleton = draw_skeleton_from_landmarks(pts, w, h)

                    t_pred0 = time.perf_counter()
                    pred, top1, margin = predict_letter_from_skeleton_and_landmarks(skeleton, pts, pts2=None, mode="ASL")
                    t_pred1 = time.perf_counter()
                    pred_ran = True

                    conf_thresh = 0.60
                    margin_thresh = 0.10
                    confident = (top1 >= conf_thresh) and (margin >= margin_thresh)

                    if pred and pred not in ("?", " ") and confident:
                        sess["pred_window"].append(pred)
                    else:
                        sess["pred_window"].clear()

                    voted = ""
                    if len(sess["pred_window"]) >= 3:
                        voted = Counter(sess["pred_window"]).most_common(1)[0][0]

                    current_char = voted or (pred if pred and pred not in ("?", " ") else "")

                    if voted and voted != sess["last_committed"]:
                        sess["transcript"] += voted
                        sess["last_committed"] = voted
                        sess["pred_window"].clear()
            # Send back prediction
            t_end = time.perf_counter()
            await websocket.send_json(
                {
                    "frameId": frame_id,
                    "clientTs": client_ts,
                    "timingMs": {
                        "decode": (t_decode - t0) * 1000.0,
                        "detect": (t_detect - t_decode) * 1000.0,
                        "predict": ((t_pred1 - t_pred0) * 1000.0) if pred_ran else 0.0,
                        "total": (t_end - t0) * 1000.0,
                    },
                    "currentChar": current_char,
                    "transcript": sessions[session_id]["transcript"],
                    "inputMode": input_mode,
                    "modelAvailable": bool(getattr(model_manager, "is_model_available", lambda *_: False)("ASL")),
                    "overlay": overlay,
                }
            )
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
        sessions.pop(session_id, None)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        sessions.pop(session_id, None)

@app.get("/")
async def root():
    return HTMLResponse("<h1>HandTalk Inference API is running</h1>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
