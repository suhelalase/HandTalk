#!/usr/bin/env python3
"""
Train ASL 26-Letter Model from ISL_Dataset
This trains a CNN that directly recognizes all 26 ASL letters (A-Z)
instead of 8 gesture groups.
"""

import os
import sys
from pathlib import Path
import numpy as np
import cv2
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.layers import Conv2D, Dense, Dropout, Flatten, MaxPooling2D
from tensorflow.keras.models import Sequential
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATASET_PATH = PROJECT_ROOT / "ISL_Dataset"
OUTPUT_MODEL_PATH = PROJECT_ROOT / "cnn_26letters_asl_model.h5"

IMAGE_SIZE = 400
BATCH_SIZE = 16
EPOCHS = 100
VALIDATION_SPLIT = 0.2

print("\n" + "="*70)
print("ASL 26-LETTER CNN MODEL TRAINING")
print("="*70)
print(f"Dataset: {DATASET_PATH}")
print(f"Output: {OUTPUT_MODEL_PATH}")
print(f"Image Size: {IMAGE_SIZE}x{IMAGE_SIZE}")
print(f"Batch Size: {BATCH_SIZE}")
print(f"Epochs: {EPOCHS}\n")


def load_dataset():
    """Load images from dataset folders (one folder per letter)"""
    images = []
    labels = []
    label_map = {}
    current_label = 0

    # Get all letter folders (A-Z)
    letter_folders = sorted([f for f in DATASET_PATH.iterdir() if f.is_dir()])

    print(f"Found {len(letter_folders)} letter folders\n")
    print("Loading images:")

    for folder in letter_folders:
        letter = folder.name
        label_map[letter] = current_label

        # Get all image files
        image_files = list(folder.glob("*.jpg")) + list(folder.glob("*.png"))

        if len(image_files) == 0:
            print(f"  ⚠️  {letter}: NO IMAGES")
            current_label += 1
            continue

        print(f"  {letter}: {len(image_files):3d} images", end="")

        loaded_count = 0
        for img_file in image_files:
            try:
                # Read image in color
                img = cv2.imread(str(img_file), cv2.IMREAD_COLOR)
                if img is None:
                    continue

                # Resize to 400x400
                img = cv2.resize(img, (IMAGE_SIZE, IMAGE_SIZE))

                # Normalize to [0, 1]
                img = img.astype("float32") / 255.0

                images.append(img)
                labels.append(current_label)
                loaded_count += 1

            except Exception as e:
                pass

        print(f" → loaded {loaded_count}")
        current_label += 1

    print(f"\n✅ Total images loaded: {len(images)}")
    print(f"✅ Total classes: {len(label_map)}")
    print(f"✅ Label map: {dict(sorted(label_map.items()))}\n")

    return np.array(images), np.array(labels), label_map


def build_model(num_classes):
    """Build improved CNN model"""
    model = Sequential([
        # Block 1
        Conv2D(32, (3, 3), activation="relu", padding="same", input_shape=(IMAGE_SIZE, IMAGE_SIZE, 3)),
        Conv2D(32, (3, 3), activation="relu", padding="same"),
        MaxPooling2D((2, 2)),
        Dropout(0.25),

        # Block 2
        Conv2D(64, (3, 3), activation="relu", padding="same"),
        Conv2D(64, (3, 3), activation="relu", padding="same"),
        MaxPooling2D((2, 2)),
        Dropout(0.25),

        # Block 3
        Conv2D(128, (3, 3), activation="relu", padding="same"),
        Conv2D(128, (3, 3), activation="relu", padding="same"),
        MaxPooling2D((2, 2)),
        Dropout(0.25),

        # Block 4
        Conv2D(256, (3, 3), activation="relu", padding="same"),
        Conv2D(256, (3, 3), activation="relu", padding="same"),
        MaxPooling2D((2, 2)),
        Dropout(0.25),

        # Dense layers
        Flatten(),
        Dense(512, activation="relu"),
        Dropout(0.5),
        Dense(256, activation="relu"),
        Dropout(0.5),
        Dense(128, activation="relu"),
        Dropout(0.3),
        Dense(num_classes, activation="softmax")
    ])

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )

    return model


def train():
    """Train the model"""

    # Check dataset
    if not DATASET_PATH.exists():
        print(f"❌ Dataset not found: {DATASET_PATH}")
        return

    # Load dataset
    print("📥 Loading dataset...")
    X, y, label_map = load_dataset()

    if len(X) == 0:
        print("❌ No images found!")
        return

    # Split dataset
    print("🔀 Splitting dataset...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=VALIDATION_SPLIT, random_state=42, stratify=y
    )
    print(f"  Training samples: {len(X_train)}")
    print(f"  Testing samples: {len(X_test)}\n")

    # Build model
    print("🏗️  Building model...")
    num_classes = len(label_map)
    model = build_model(num_classes)
    print(model.summary())

    # Data augmentation for better generalization
    train_datagen = ImageDataGenerator(
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        zoom_range=0.15,
        horizontal_flip=False,  # Don't flip hand signs
        fill_mode="nearest",
        brightness_range=[0.9, 1.1]
    )

    # Train model
    print("\n🎓 Training model...")
    print("(This may take 10-30 minutes depending on your hardware)\n")

    history = model.fit(
        train_datagen.flow(X_train, y_train, batch_size=BATCH_SIZE),
        epochs=EPOCHS,
        validation_data=(X_test, y_test),
        steps_per_epoch=len(X_train) // BATCH_SIZE,
        verbose=1
    )

    # Evaluate
    print("\n📊 Evaluating model...")
    test_loss, test_accuracy = model.evaluate(X_test, y_test)
    print(f"  Test Accuracy: {test_accuracy*100:.2f}%")
    print(f"  Test Loss: {test_loss:.4f}\n")

    # Save model
    print(f"💾 Saving model to {OUTPUT_MODEL_PATH}...")
    model.save(str(OUTPUT_MODEL_PATH))
    print("✅ Model saved!\n")

    # Print summary
    print("="*70)
    print("✅ TRAINING COMPLETE!")
    print("="*70)
    print(f"\nModel: {OUTPUT_MODEL_PATH}")
    print(f"Accuracy: {test_accuracy*100:.2f}%")
    print(f"Classes: {num_classes} (A-Z)")
    print(f"\nTo use this model:")
    print("1. Copy to apps/api/: cp cnn_26letters_asl_model.h5 apps/api/")
    print("2. Update model_manager.py to load this model")
    print("3. Update main.py decoder to handle 26 outputs instead of 8")
    print("4. Restart backend server")
    print("="*70 + "\n")

    return history, label_map


if __name__ == "__main__":
    try:
        train()
    except KeyboardInterrupt:
        print("\n⏹️  Training interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
