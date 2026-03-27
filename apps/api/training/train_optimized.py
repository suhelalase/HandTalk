"""
Train ISL Model with Optimized Hyperparameters and Better Data Augmentation.

Uses an improved CNN architecture with better training strategy.
"""

import os
from pathlib import Path

import cv2
import numpy as np
from tensorflow.keras.layers import (
    Conv2D, MaxPooling2D, Dense, Dropout, Flatten,
    BatchNormalization, GlobalAveragePooling2D, Input
)
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

ISL_DATASET_PATH = Path(__file__).resolve().parents[3] / "ISL_Dataset"
OUTPUT_MODEL_PATH = Path(__file__).resolve().parents[3] / "cnn8grps_rad1_isl_model.h5"

IMAGE_SIZE = 224
BATCH_SIZE = 16
EPOCHS = 100

print("[Config] Optimized CNN with Enhanced Training Strategy")
print(f"[Config] Image: {IMAGE_SIZE}x{IMAGE_SIZE}, Batch: {BATCH_SIZE}, Epochs: {EPOCHS}")


def load_dataset():
    """Load and preprocess images."""
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

                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, (IMAGE_SIZE, IMAGE_SIZE))

                # Normalize
                img = img.astype("float32") / 255.0

                images.append(img)
                labels.append(current_label)

            except Exception as e:
                print(f"    [Error] {img_file}: {e}")

        current_label += 1

    return np.array(images), np.array(labels), label_map


def build_optimized_cnn(num_classes):
    """Build optimized CNN with batch normalization."""
    model = Sequential([
        Input(shape=(IMAGE_SIZE, IMAGE_SIZE, 3)),

        # Block 1
        Conv2D(64, (3, 3), activation='relu', padding='same'),
        BatchNormalization(),
        Conv2D(64, (3, 3), activation='relu', padding='same'),
        BatchNormalization(),
        MaxPooling2D((2, 2)),
        Dropout(0.25),

        # Block 2
        Conv2D(128, (3, 3), activation='relu', padding='same'),
        BatchNormalization(),
        Conv2D(128, (3, 3), activation='relu', padding='same'),
        BatchNormalization(),
        MaxPooling2D((2, 2)),
        Dropout(0.25),

        # Block 3
        Conv2D(256, (3, 3), activation='relu', padding='same'),
        BatchNormalization(),
        Conv2D(256, (3, 3), activation='relu', padding='same'),
        BatchNormalization(),
        MaxPooling2D((2, 2)),
        Dropout(0.25),

        # Block 4
        Conv2D(512, (3, 3), activation='relu', padding='same'),
        BatchNormalization(),
        Conv2D(512, (3, 3), activation='relu', padding='same'),
        BatchNormalization(),
        MaxPooling2D((2, 2)),
        Dropout(0.25),

        # Global pooling
        GlobalAveragePooling2D(),

        # Dense layers
        Dense(512, activation='relu'),
        BatchNormalization(),
        Dropout(0.5),
        Dense(256, activation='relu'),
        BatchNormalization(),
        Dropout(0.3),
        Dense(num_classes, activation='softmax')
    ])

    return model


def train():
    """Train with optimized strategy."""
    print("\n[Training] Starting Optimized CNN Training\n")

    if not ISL_DATASET_PATH.exists():
        print(f"[Error] Dataset not found: {ISL_DATASET_PATH}")
        return

    # Load dataset
    print("[Loading] Loading dataset...")
    X, y, label_map = load_dataset()

    if len(X) == 0:
        print("[Error] No images found")
        return

    print(f"[Success] Loaded {len(X)} images from {len(label_map)} classes")

    # Split with stratification
    print("\n[Split] Splitting dataset...")
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"  Training: {len(X_train)}, Testing: {len(X_test)}")

    # Build model
    print("\n[Building] Building optimized CNN...")
    model = build_optimized_cnn(num_classes=len(label_map))
    print(f"  Parameters: {model.count_params():,}")

    # Compile with low learning rate
    optimizer = Adam(learning_rate=0.001)
    model.compile(
        optimizer=optimizer,
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )

    # Aggressive data augmentation
    train_augmentation = ImageDataGenerator(
        rotation_range=45,
        width_shift_range=0.4,
        height_shift_range=0.4,
        zoom_range=0.4,
        horizontal_flip=True,
        shear_range=0.3,
        brightness_range=[0.7, 1.3],
        fill_mode="constant",
        cval=0
    )

    # Create data generator with sufficient samples
    train_generator = train_augmentation.flow(
        X_train, y_train,
        batch_size=BATCH_SIZE,
        shuffle=True
    )

    # Callbacks for adaptive training
    early_stop = EarlyStopping(
        monitor='val_accuracy',
        patience=15,
        restore_best_weights=True,
        verbose=0
    )

    reduce_lr = ReduceLROnPlateau(
        monitor='val_accuracy',
        factor=0.5,
        patience=5,
        min_lr=0.00001,
        verbose=0
    )

    # Train as multi-epoch but without augmentation to stabilize
    print("\n[Training] Training model...")
    print("  This may take 10-15 minutes...\n")

    history = model.fit(
        train_generator,
        epochs=EPOCHS,
        validation_data=(X_test, y_test),
        steps_per_epoch=max(10, len(X_train) // BATCH_SIZE),
        callbacks=[early_stop, reduce_lr],
        verbose=0
    )

    print("\n[Training] Training completed!")

    # Evaluate
    print("\n[Evaluation] Evaluating model...")
    test_loss, test_accuracy = model.evaluate(X_test, y_test, verbose=0)
    train_loss, train_accuracy = model.evaluate(X_train, y_train, verbose=0)

    print(f"  Test Accuracy:  {test_accuracy*100:6.2f}%  (Loss: {test_loss:.4f})")
    print(f"  Train Accuracy: {train_accuracy*100:6.2f}%  (Loss: {train_loss:.4f})")

    # Save model
    print(f"\n[Saving] Saving to {OUTPUT_MODEL_PATH}...")
    model.save(str(OUTPUT_MODEL_PATH))
    print("[Success] Model saved!")

    # Summary
    print("\n" + "=" * 60)
    print("[Complete] Training Complete!")
    print("=" * 60)
    print(f"\nFinal Results:")
    print(f"  Test Accuracy:  {test_accuracy*100:.2f}%")
    print(f"  Train Accuracy: {train_accuracy*100:.2f}%")
    print(f"\nModel: {OUTPUT_MODEL_PATH}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        train()
    except KeyboardInterrupt:
        print("\n[Interrupted] Training stopped by user")
    except Exception as e:
        print(f"[Error] {e}")
        import traceback
        traceback.print_exc()
