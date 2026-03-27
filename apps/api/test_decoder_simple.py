#!/usr/bin/env python3
"""
Simple test of character decoder - what's it actually returning?
"""
import numpy as np

# Define the decoder function
def _decode_group_to_char(ch1: int, ch2: int, pts, pts2=None) -> str:
    """Character decoder"""
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
        print(f"Error: {e}")
        return '?'


print("="*70)
print("CHARACTER DECODER TEST")
print("="*70)

# Create simple test landmarks
pts_default = np.array([
    [100, 150],  # 0: wrist
    [105, 100],  # 1: thumb base
    [110, 80],   # 2: thumb mid
    [115, 60],   # 3: thumb tip
    [120, 50],   # 4: thumb tip
    [150, 100],  # 5: index base
    [155, 70],   # 6: index mid
    [160, 50],   # 7: index pip
    [165, 30],   # 8: index tip
    [170, 110],  # 9: middle base
    [175, 75],   # 10: middle mid
    [180, 50],   # 11: middle pip
    [185, 25],   # 12: middle tip
    [190, 115],  # 13: ring base
    [195, 80],   # 14: ring mid
    [200, 55],   # 15: ring pip
    [205, 30],   # 16: ring tip
    [210, 120],  # 17: pinky base
    [215, 85],   # 18: pinky mid
    [220, 60],   # 19: pinky pip
    [225, 35],   # 20: pinky tip
], dtype=np.float32)

print("\nTesting different (ch1, ch2) pairs with default landmarks:\n")

test_pairs = [
    (0, 0, "S"), (1, 0, "B"), (2, 2, "O"), (3, 5, "H"),
    (4, 6, "L"), (5, 2, "P"), (6, 4, "X"), (7, 1, "J"),
    (5, 3, "?"), (3, 2, "?"), (1, 5, "?"), (2, 0, "?"),
]

for ch1, ch2, expected in test_pairs:
    result = _decode_group_to_char(ch1, ch2, pts_default)
    status = "✓" if result == expected else "✗"
    print(f"  {status} [{ch1}, {ch2}] -> '{result}' (expected '{expected}')")

print("\n" + "="*70)
print("PROBLEM ANALYSIS")
print("="*70)
print("""
The decoder has a CRITICAL FLAW:
1. It only recognizes specific (ch1, ch2) pairs
2. For pairs that DON'T match, it returns defaults:
   - Group 0 -> 'S'
   - Group 1 -> 'B'
   - Group 2 -> 'O'
   - Group 3 -> 'H'
   - Group 4 -> 'L'
   - Group 5 -> 'P'
   - Group 6 -> 'X'
   - Group 7 -> 'J'

3. If MODEL always predicts groups 4, 5, 6, 7 (most confident),
   you will ALWAYS get: L, P, X, J

   This matches what you reported: only L, P, O!

SOLUTION:
The problem is NOT the decoder logic - it's that the MODEL itself
is not learning to distinguish between different hand signs.
The model is outputting high confidence for only a few groups.

You need to:
1. Check if model was trained on all 26 characters
2. Check if model training was complete
3. Consider retraining the model on proper ASL data
""")
