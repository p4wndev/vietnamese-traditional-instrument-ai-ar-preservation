"""
ML utility functions shared across services.
"""

import cv2
import numpy as np


# ── Instrument label mapping ───────────────────────────────────────────────

INSTRUMENT_CATEGORIES = [
    "cong_chieng",
    "dan_bau",
    "dan_co",
    "dan_da",
    "dan_day",
    "dan_nguyet",
    "dan_sen",
    "dan_t_rung",
    "dan_tinh",
    "dan_tranh",
    "dan_ty_ba",
    "guitar",
    "khen",
    "trong_quan",
]

INSTRUMENT_DISPLAY_NAMES = {
    "cong_chieng": "cồng_chiêng",
    "dan_bau": "đàn_bầu",
    "dan_co": "đàn_cò",
    "dan_da": "đàn_đá",
    "dan_day": "đàn_đáy",
    "dan_nguyet": "đàn_nguyệt",
    "dan_sen": "đàn_sến",
    "dan_t_rung": "đàn_t_rưng",
    "dan_tinh": "đàn_tính",
    "dan_tranh": "đàn_tranh",
    "dan_ty_ba": "đàn_tỳ_bà",
    "guitar": "guitar",
    "khen": "khèn",
    "trong_quan": "trống_quân",
}


def build_lenet_model(input_shape=(64, 64, 3), num_classes: int = 14):
    """Build the LeNet-5 architecture used during training."""
    import tensorflow as tf

    model = tf.keras.Sequential(
        [
            tf.keras.layers.Conv2D(6, (5, 5), strides=(1, 1), activation="tanh", input_shape=input_shape),
            tf.keras.layers.AveragePooling2D(pool_size=(2, 2), strides=(2, 2)),
            tf.keras.layers.Conv2D(6, (5, 5), strides=(1, 1), activation="tanh"),
            tf.keras.layers.AveragePooling2D(pool_size=(2, 2), strides=(2, 2)),
            tf.keras.layers.Dense(120, activation="tanh"),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(84, activation="tanh"),
            tf.keras.layers.Dense(num_classes, activation="softmax"),
        ]
    )
    return model


def preprocess_for_lenet(image: np.ndarray, size: int = 64) -> np.ndarray:
    """Resize and normalise a BGR image crop for LeNet inference."""
    resized = cv2.resize(image, (size, size))
    normalised = resized.astype("float32") / 255.0
    return np.expand_dims(normalised, axis=0)  # shape: (1, size, size, 3)


def generate_color_for_class(class_id: int) -> tuple:
    """Deterministic BGR colour per class id."""
    import random

    rng = random.Random(class_id * 31337)
    return (rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))
