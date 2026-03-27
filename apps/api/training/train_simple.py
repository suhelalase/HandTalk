"""
Train ISL Model with Simple Direct Training (No Generator).

Uses direct fit() method for reliable training without data generator issues.
"""

import os
from pathlib import Path
import cv2
import numpy as np
from tensorflow.keras.layers import (
    Conv2D, MaxPooling2D, Dense, Dropout, Flatten,
    BatchNormalization, Input, GlobalAveragePooling2D
)
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.model_selection import train_test_split

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

ISL_DATASET_PATH = Path(__file__).resolve().parents[3] / "ISL_Dataset"
OUTPUT_MODEL_PATH = Path(__file__).resolve().parents[3] / "cnn8grps_rad1_isl_model.h5"

IMAGE_SIZE = 224
BATCH_SIZE = 16
EPOCHS = 40

print("\n[Config] Simple CNN Training")
print(f"[Config] Image: {IMAGE_SIZE}x{IMAGE_SIZE}, Batch: {BATCH_SIZE}, Epochs: {EPOCHS}\n")


def load_dataset():
    """Load images."""
    images = []
    labels = []
    label_map = {}
    current_label = 0

    letter_folders = sorted(
        [f for f in ISL_DATASET_PATH.iterdir() if f.is_dir()]
    )

    print(f"[Dataset] Found {len(letter_folders)} folders")

    for folder in letter_folders:
        letter = folder.name
        label_map[letter] = current_label
        img_files = sorted(list(folder.glob("*.jpg")) + list(folder.glob("*.png")))
        print(f"  {letter}: {len(img_files)} images")

        for img_file in img_files:
            try:
                img = cv2.imread(str(img_file), cv2.IMREAD_COLOR)
                if img is None:
                    continue
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, (IMAGE_SIZE, IMAGE_SIZE))
                img = img.astype("float32") / 255.0
                images.append(img)
                labels.append(current_label)
            except:
                pass

        current_label += 1

    return np.array(images), np.array(labels), label_map


def build_cnn(num_classes):
    """Build CNN model."""
    model = Sequential([
        Input(shape=(IMAGE_SIZE, IMAGE_SIZE, 3)),
        Conv2D(64, 3, padding='same', activation='relu'),
        BatchNormalization(),
        Conv2D(64, 3, padding='same', activation='relu'),
        BatchNormalization(),
        MaxPooling2D(2),
        Dropout(0.25),

        Conv2D(128, 3, padding='same', activation='relu'),
        BatchNormalization(),
        Conv2D(128, 3, padding='same', activation='relu'),
        BatchNormalization(),
        MaxPooling2D(2),
        Dropout(0.25),

        Conv2D(256, 3, padding='same', activation='relu'),
        BatchNormalization(),
        Conv2D(256, 3, padding='same', activation='relu'),
        BatchNormalization(),
        MaxPooling2D(2),
        Dropout(0.25),

        Conv2D(512, 3, padding='same', activation='relu'),
        BatchNormalization(),
        Conv2D(512, 3, padding='same', activation='relu'),
        BatchNormalization(),
        MaxPooling2D(2),
        Dropout(0.25),

        GlobalAveragePooling2D(),
        Dense(512, activation='relu'),
        BatchNormalization(),
        Dropout(0.5),
        Dense(256, activation='relu'),
        BatchNormalization(),
        Dropout(0.3),
        Dense(num_classes, activation='softmax')
    ])

    return model


def augment_images(images):
    """Simple data augmentation."""
    from tensorflow.image import (
        rot90, flip_left_right, random_brightness
    )
    import tensorflow as tf

    augmented = []
    for img in images:
        img_tf = tf.convert_to_tensor(img)

        # Random rotations
        if np.random.rand() > 0.5:
            img_tf = tf.image.rot90(img_tf, k=np.random.randint(1, 4))

        # Random flip
        if np.random.rand() > 0.5:
            img_tf = tf.image.flip_left_right(img_tf)

        # Random brightness
        if np.random.rand() > 0.5:
            img_tf = tf.image.adjust_brightness(
                img_tf,
                delta=np.random.uniform(-0.3, 0.3)
            )

        augmented.append(img_tf.numpy())

    return np.array(augmented)


def train():
    """Train model."""
    print("[Training] Starting ISL CNN Training\n")

    if not ISL_DATASET_PATH.exists():
        print(f"[Error] Dataset not found")
        return

    print("[Loading] Loading dataset...")
    X, y, label_map = load_dataset()

    if len(X) == 0:
        print("[Error] No images loaded")
        return

    print(f"[Success] Loaded {len(X)} images from {len(label_map)} classes\n")

    # Split dataset
    print(f"[Split] Splitting dataset (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"  Training: {len(X_train)}, Testing: {len(X_test)}\n")

    # Augment training data
    print("[Augment] Augmenting training data...")
    X_train_aug = augment_images(X_train)
    print(f"  Augmented to {len(X_train_aug)} images\n")

    # Build model
    print("[Building] Building CNN model...")
    model = build_cnn(num_classes=len(label_map))
    print(f"  Parameters: {model.count_params():,}\n")

    # Compile
    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )

    # Callbacks
    early_stop = EarlyStopping(
        monitor='val_accuracy',
        patience=10,
        restore_best_weights=True,
        verbose=0
    )

    reduce_lr = ReduceLROnPlateau(
        monitor='val_accuracy',
        factor=0.5,
        patience=3,
        min_lr=0.00001,
        verbose=0
    )

    # Train
    print("[Training] Training model...")
    print("  This may take 5-10 minutes...\n")

    history = model.fit(
        X_train_aug,
        y_train,
        batch_size=BATCH_SIZE,
        epochs=EPOCHS,
        validation_data=(X_test, y_test),
        callbacks=[early_stop, reduce_lr],
        verbose=0
    )

    print("\n[Training] Training completed!")

    # Evaluate
    print("\n[Evaluation] Final Evaluation:")
    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
    train_loss, train_acc = model.evaluate(X_train, y_train, verbose=0)

    print(f"  Test Accuracy:  {test_acc*100:6.2f}%")
    print(f"  Train Accuracy: {train_acc*100:6.2f}%")

    # Save
    print(f"\n[Saving] Saving model...")
    model.save(str(OUTPUT_MODEL_PATH))
    print("[Success] Model saved!\n")

    # Summary
    print("=" * 60)
    print("[Complete] Training Complete!")
    print("=" * 60)
    print(f"\nResults:")
    print(f"  Test Accuracy:  {test_acc*100:.2f}%")
    print(f"  Train Accuracy: {train_acc*100:.2f}%")
    print(f"\nModel saved to: {OUTPUT_MODEL_PATH}")
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    try:
        train()
    except KeyboardInterrupt:
        print("\n[Interrupted] Training stopped")
    except Exception as e:
        print(f"[Error] {e}")
        import traceback
        traceback.print_exc()
