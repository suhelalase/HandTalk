#!/usr/bin/env python3
"""
Comprehensive debugging script to identify prediction issues.
"""
import sys
sys.path.insert(0, '/z/HandTalk/apps/api')

import numpy as np
from main import _decode_group_to_char, distance

print("="*60)
print("HANDTALK DECODER DEBUGGING")
print("="*60)

# Test 1: Check distance function
print("\n1. Testing distance function:")
p1 = [0, 0]
p2 = [3, 4]
dist = distance(p1, p2)
print(f"   Distance([0,0], [3,4]) = {dist} (expected 5.0)")
assert abs(dist - 5.0) < 0.1, "Distance calculation broken!"
print("   ✅ Distance function works\n")

# Test 2: Check Group 2 (C vs O)
print("2. Testing Group 2 (C, O):")
pts_c = [[0]*2 for _ in range(21)]
pts_c[4] = [10, 50]   # thumb
pts_c[12] = [60, 50]  # middle tip - far
result_c = _decode_group_to_char(2, 0, pts_c)
print(f"   Large distance -> {result_c} (expected C)")

pts_o = [[0]*2 for _ in range(21)]
pts_o[4] = [10, 50]   # thumb
pts_o[12] = [30, 50]  # middle tip - close
result_o = _decode_group_to_char(2, 0, pts_o)
print(f"   Small distance -> {result_o} (expected O)")
print()

# Test 3: Check if pts is None
print("3. Testing None handling:")
try:
    result = _decode_group_to_char(1, 0, None)
    print(f"   With None pts: {result}")
except Exception as e:
    print(f"   ❌ Error with None: {e}")
print()

# Test 4: Check simple Group 0 patterns
print("4. Testing Group 0 (A, E, M, N, S, T):")
# A: thumb left of fingers
pts_a = [[0]*2 for _ in range(21)]
pts_a[4] = [10, 50]   # thumb - far left
pts_a[6] = [50, 50]   # index
pts_a[10] = [50, 50]  # middle
pts_a[14] = [50, 50]  # ring
pts_a[18] = [50, 50]  # pinky
result_a = _decode_group_to_char(0, 0, pts_a)
print(f"   Thumb left -> {result_a} (expected A)")
print()

# Test 5: Check Group 1 patterns
print("5. Testing Group 1 (B, D, F, I, K, R, U, V, W):")

# B: all fingers extended down (all PIP > TIP)
pts_b = [[j, j] for j in range(21)]
pts_b[6] = [10, 20]   # Index PIP > Index TIP (down)
pts_b[8] = [10, 10]
pts_b[10] = [20, 30]  # Middle PIP > Middle TIP
pts_b[12] = [20, 20]
pts_b[14] = [30, 40]  # Ring PIP > Ring TIP
pts_b[16] = [30, 30]
pts_b[18] = [40, 50]  # Pinky PIP > Pinky TIP
pts_b[20] = [40, 40]
result_b = _decode_group_to_char(1, 0, pts_b)
print(f"   All down -> {result_b} (expected B)")

# F: Index extended, rest down
pts_f = [[0]*2 for _ in range(21)]
pts_f[6] = [10, 10]   # Index PIP < Index TIP (up/extended)
pts_f[8] = [10, 20]
pts_f[10] = [20, 30]  # Middle PIP > Middle TIP (down)
pts_f[12] = [20, 20]
pts_f[14] = [30, 40]  # Ring PIP > Ring TIP (down)
pts_f[16] = [30, 30]
pts_f[18] = [40, 50]  # Pinky PIP > Pinky TIP (down)
pts_f[20] = [40, 40]
result_f = _decode_group_to_char(1, 0, pts_f)
print(f"   Index up, rest down -> {result_f} (expected F)")

print("\n" + "="*60)
print("If all tests show expected values, decoder is working!")
print("="*60)
