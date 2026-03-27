#!/usr/bin/env python3
"""
Quick test to verify character prediction is working.
Run: python test_decoder.py
"""
import sys
sys.path.insert(0, '/z/HandTalk/apps/api')

from main import _decode_group_to_char

# Test patterns - simple finger down/up positions
# Format: (ch1, ch2, pts, expected_char)

tests = [
    # Group 2: C vs O (distance based)
    (2, 0, {4: [10, 50], 12: [40, 50]}, 'O'),  # Close = O

    # Group 3: G vs H (distance based)
    (3, 0, {8: [10, 50], 12: [50, 50]}, 'H'),  # Close = H

    # Group 7: Y vs J (distance based)
    (7, 0, {8: [10, 50], 4: [50, 50]}, 'J'),   # Close = J

    # Group 4: L (no ambiguity)
    (4, 0, {}, 'L'),

    # Group 6: X (no ambiguity)
    (6, 0, {}, 'X'),

    # Group 0
    (0, 0, {4: [10, 50], 6: [15, 50], 10: [20, 50], 14: [25, 50], 18: [30, 50]}, 'A'),  # Thumb left
]

print("Testing character decoder...\n")

for i, (ch1, ch2, pts_dict, expected) in enumerate(tests):
    # Create realistic landmark array
    pts = [[j*5, j*5] for j in range(21)]

    # Update with test values
    for idx, pos in pts_dict.items():
        if idx < 21:
            pts[idx] = pos

    result = _decode_group_to_char(ch1, ch2, pts)
    status = "✅" if result == expected else "❌"
    print(f"Test {i+1}: group {ch1} -> {result} (expected {expected}) {status}")

print("\nIf you see ✅ for all tests, decoder is working!")
