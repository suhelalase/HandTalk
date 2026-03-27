#!/usr/bin/env python3
"""Wrapper to run training with proper encoding."""

import os
import sys
import io

# Set encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Monkey-patch sys.stdout to handle encoding errors gracefully
class UTF8StreamWrapper(io.TextIOWrapper):
    def write(self, s):
        try:
            return super().write(s)
        except UnicodeEncodeError:
            # Replace problematic characters
            s = s.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
            return super().write(s)

# Try to wrap stdout
try:
    sys.stdout = UTF8StreamWrapper(
        sys.stdout.buffer,
        encoding='utf-8',
        errors='replace',
        write_through=True
    )
except:
    pass

# Now import and run training
from pathlib import Path
from train_isl_model import train

if __name__ == "__main__":
    try:
        train()
    except KeyboardInterrupt:
        print("\n[Interrupted] Training interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"[Error] Error during training: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
