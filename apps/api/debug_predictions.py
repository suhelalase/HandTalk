"""
Debug script to test character predictions and identify patterns.
Run this to see what characters are being predicted for test inputs.
"""
import sys
from pathlib import Path
import numpy as np

sys.path.append(str(Path(__file__).resolve().parent))

from main import _decode_group_to_char, distance

# Test patterns from ASL alphabet
test_data = {
    # Group 0 [AEMNST]
    'A': {'ch1': 0, 'pts': [[0, 0], [0, 0], [0, 0], [0, 0], [10, 50], [70, 100], [72, 102], [74, 104], [76, 106], [80, 100], [82, 102], [84, 104], [86, 106], [90, 100], [92, 102], [94, 104], [96, 106], [100, 100], [102, 102], [104, 104], [106, 106]]},
    'E': {'ch1': 0, 'pts': [[0, 0], [0, 0], [0, 0], [0, 0], [50, 150], [70, 100], [72, 102], [74, 50], [76, 40], [80, 100], [82, 102], [84, 50], [86, 40], [90, 100], [92, 102], [94, 50], [96, 40], [100, 100], [102, 102], [104, 50], [106, 40]]},
    'S': {'ch1': 0, 'pts': [[0, 0], [0, 0], [0, 0], [0, 0], [50, 50], [70, 100], [72, 102], [74, 104], [76, 106], [80, 100], [82, 102], [84, 104], [86, 106], [90, 100], [92, 102], [94, 104], [96, 106], [100, 100], [102, 102], [104, 104], [106, 106]]},
}

# Group 1 [BFDIUVWKR]
b_pts = [[0, 0], [0, 0], [0, 0], [0, 0], [50, 50],  # thumb
         [70, 100], [72, 110], [74, 120], [76, 130],  # index - all down
         [80, 100], [82, 110], [84, 120], [86, 130],  # middle - all down
         [90, 100], [92, 110], [94, 120], [96, 130],  # ring - all down
         [100, 100], [102, 110], [104, 120], [106, 130]]  # pinky - all down

f_pts = [[0, 0], [0, 0], [0, 0], [0, 0], [50, 50],  # thumb
         [70, 80], [72, 70], [74, 60], [76, 50],    # index - extended (tip < pip)
         [80, 100], [82, 110], [84, 120], [86, 130], # middle - down (tip > pip)
         [90, 100], [92, 110], [94, 120], [96, 130], # ring - down
         [100, 100], [102, 110], [104, 120], [106, 130]]  # pinky - down

# Test the decoder
print("Testing character predictions:\n")
for ch_name, ch_data in test_data.items():
    ch1, ch2 = ch_data['ch1'], 0
    pts = ch_data['pts']
    pred = _decode_group_to_char(ch1, ch2, pts)
    print(f"{ch_name:5} (group {ch1}, ch2={ch2}) -> predicted: {pred}")

print("\nTesting Group 1 variations:")
# Test B
pred_b = _decode_group_to_char(1, 0, b_pts)
print(f"B pattern -> {pred_b}")

# Test F
pred_f = _decode_group_to_char(1, 0, f_pts)
print(f"F pattern -> {pred_f}")

# Check finger positions for F
print(f"\nF pattern details:")
print(f"  pts[6][1] ({f_pts[6][1]}) < pts[8][1] ({f_pts[8][1]}): {f_pts[6][1] < f_pts[8][1]} (index extended)")
print(f"  pts[10][1] ({f_pts[10][1]}) > pts[12][1] ({f_pts[12][1]}): {f_pts[10][1] > f_pts[12][1]} (middle down)")
print(f"  pts[14][1] ({f_pts[14][1]}) > pts[16][1] ({f_pts[16][1]}): {f_pts[14][1] > f_pts[16][1]} (ring down)")
print(f"  pts[18][1] ({f_pts[18][1]}) > pts[20][1] ({f_pts[20][1]}): {f_pts[18][1] > f_pts[20][1]} (pinky down)")
