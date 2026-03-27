"""
Train ISL Model using Transfer Learning with MobileNetV2.

Uses pre-trained MobileNetV2 for much better accuracy with limited data.
"""

import os
from pathlib import Path

import cv2
import numpy as np
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, Dropout, GlobalAveragePooling2D
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Configuration
ISL_DATASET_PATH = Path(__file__).resolve().parents[3] / "ISL_Dataset"
OUTPUT_MODEL_PATH = Path(__file__).resolve().parents[3] / "cnn8grps_rad1_isl_model.h5"

IMAGE_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 50
LEARNING_RATE = 0.001

print(f"[Config] Image size: {IMAGE_SIZE}x{IMAGE_SIZE}")
print(f"[Config] Batch size: {BATCH_SIZE}, Epochs: {EPOCHS}")
print(f"[Config] Output model: {OUTPUT_MODEL_PATH}")


def load_dataset():
    """Load images and labels from ISL_Dataset folder."""
    images = []
    labels = []
    label_map = {}
    current_label = 0

    letter_folders = sorted(
        [folder for folder in ISL_DATASET_PATH.iterdir() if folder.is_dir()]
    )

    print(f"\n[Dataset] Found {len(letter_folders)} letter folders")

    for folder in letter_folders:
        letter = folder.name
        label_map[letter] = current_label

        image_files = list(folder.glob("*.jpg")) + list(folder.glob("*.png"))
        print(f"  {letter}: {len(image_files)} images")

        for img_file in image_files:
            try:
                img = cv2.imread(str(img_file), cv2.IMREAD_COLOR)
                if img is None:
                    continue

                # Convert BGR to RGB
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                # Resize to 224x224
                img = cv2.resize(img, (IMAGE_SIZE, IMAGE_SIZE))

                # Normalize to 0-1
                img = img.astype("float32") / 255.0

                images.append(img)
                labels.append(current_label)

            except Exception as e:
                print(f"    [Error] Error loading {img_file}: {e}")

        current_label += 1

    return np.array(images), np.array(labels), label_map


def build_transfer_model(num_classes):
    """Build model using MobileNetV2 transfer learning."""

    # Suppress download progress output
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    import logging
    logging.getLogger('tensorflow').setLevel(logging.ERROR)

    print("\n  Downloading pre-trained MobileNetV2 weights...")
    print("  (This happens only once)...")

    # Load pre-trained MobileNetV2 (without top classification layer)
    try:
        base_model = MobileNetV2(
            input_shape=(IMAGE_SIZE, IMAGE_SIZE, 3),
            include_top=False,
            weights='imagenet'
        )
    except Exception as e:
        print(f"  [Warning] Could not download weights: {e}")
        print("  Using randomly initialized model instead...")
        base_model = MobileNetV2(
            input_shape=(IMAGE_SIZE, IMAGE_SIZE, 3),
            include_top=False,
            weights=None
        )

    # Freeze base model weights initially
    base_model.trainable = False

    # Add custom classification head
    inputs = base_model.input
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(256, activation='relu')(x)
    x = Dropout(0.5)(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.3)(x)
    outputs = Dense(num_classes, activation='softmax')(x)

    model = Model(inputs=inputs, outputs=outputs)

    # Compile with low learning rate
    optimizer = Adam(learning_rate=LEARNING_RATE)
    model.compile(
        optimizer=optimizer,
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )

    return model, base_model


def train():
    """Train ISL model using transfer learning."""
    print("\n[Training] Starting ISL Model Training (Transfer Learning)\n")

    if not ISL_DATASET_PATH.exists():
        print(f"[Error] Dataset folder not found: {ISL_DATASET_PATH}")
        return

    # Load dataset
    print("[Loading] Loading dataset...")
    X, y, label_map = load_dataset()

    if len(X) == 0:
        print("[Error] No images found in dataset")
        return

    print(f"[Success] Loaded {len(X)} images")
    print(f"  Classes: {len(label_map)} ({', '.join(sorted(label_map.keys()))})")

    # Split dataset
    print("\n[Split] Splitting dataset...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"  Training: {len(X_train)} images")
    print(f"  Testing: {len(X_test)} images")

    # Build model
    print("\n[Building] Building transfer learning model...")
    model, base_model = build_transfer_model(num_classes=len(label_map))
    print(f"  Model built with {model.count_params():,} total parameters")
    print(f"  Base model (frozen): {base_model.count_params():,} parameters")

    # Data augmentation for training
    train_datagen = ImageDataGenerator(
        rotation_range=30,
        width_shift_range=0.3,
        height_shift_range=0.3,
        zoom_range=0.3,
        horizontal_flip=True,
        shear_range=0.2,
        fill_mode="nearest",
    )

    # Stage 1: Train top layers with frozen base model
    print("\n[Training] Stage 1: Training top layers (frozen base model)...")
    print("  This may take 5-10 minutes...")

    history1 = model.fit(
        train_datagen.flow(X_train, y_train, batch_size=BATCH_SIZE),
        epochs=EPOCHS // 2,
        validation_data=(X_test, y_test),
        steps_per_epoch=len(X_train) // BATCH_SIZE,
        verbose=0
    )

    # Stage 2: Unfreeze some layers and fine-tune
    print("[Training] Stage 2: Fine-tuning base model layers...")

    # Unfreeze last 30 layers of base model
    base_model.trainable = True
    for layer in base_model.layers[:-30]:
        layer.trainable = False

    # Recompile with lower learning rate for fine-tuning
    optimizer = Adam(learning_rate=LEARNING_RATE / 10)
    model.compile(
        optimizer=optimizer,
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )

    history2 = model.fit(
        train_datagen.flow(X_train, y_train, batch_size=BATCH_SIZE),
        epochs=EPOCHS // 2,
        validation_data=(X_test, y_test),
        steps_per_epoch=len(X_train) // BATCH_SIZE,
        verbose=0,
        initial_epoch=EPOCHS // 2
    )

    print("[Training] Training completed!")

    # Evaluate
    print("\n[Evaluation] Evaluating final model...")
    test_loss, test_accuracy = model.evaluate(X_test, y_test, verbose=0)
    print(f"  Test Accuracy: {test_accuracy:.4f} ({test_accuracy*100:.2f}%)")
    print(f"  Test Loss: {test_loss:.4f}")

    # Get training accuracy
    train_loss, train_accuracy = model.evaluate(X_train, y_train, verbose=0)
    print(f"\n  Training Accuracy: {train_accuracy:.4f} ({train_accuracy*100:.2f}%)")
    print(f"  Training Loss: {train_loss:.4f}")

    # Save model
    print(f"\n[Saving] Saving model to {OUTPUT_MODEL_PATH}...")
    model.save(str(OUTPUT_MODEL_PATH))
    print("[Success] Model saved successfully!")

    # Print summary
    print("\n" + "=" * 60)
    print("[Complete] ISL Model Training Complete!")
    print("=" * 60)
    print(f"\nModel Performance:")
    print(f"  Test Accuracy: {test_accuracy*100:.2f}%")
    print(f"  Training Accuracy: {train_accuracy*100:.2f}%")
    print(f"\nModel saved at: {OUTPUT_MODEL_PATH}")
    print("\nTo use this model:")
    print("1. Restart the backend server")
    print("2. Select 'ISL' mode in the frontend")
    print("3. ISL gestures will now be recognized with better accuracy!")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        train()
    except KeyboardInterrupt:
        print("\n[Interrupted] Training interrupted by user")
    except Exception as e:
        print(f"[Error] Error during training: {e}")
        import traceback
        traceback.print_exc()
