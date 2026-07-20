"""Reusable payload generators for Triton inputs."""

import io
from typing import List, Sequence

import numpy as np
import tritonclient.http as httpclient
from PIL import Image


def random_jpeg_bytes(size: int = 512, quality: int = 85) -> bytes:
    arr = np.random.randint(0, 256, size=(size, size, 3), dtype=np.uint8)
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def random_fp32(shape: Sequence[int]) -> np.ndarray:
    return np.random.rand(*shape).astype(np.float32)


def random_uint8(shape: Sequence[int]) -> np.ndarray:
    return np.random.randint(0, 256, size=shape, dtype=np.uint8)


def bytes_input(name: str, values: List[bytes]) -> httpclient.InferInput:
    """BYTES tensor with shape [len(values), 1]."""
    arr = np.array([[v] for v in values], dtype=object)
    inp = httpclient.InferInput(name, arr.shape, "BYTES")
    inp.set_data_from_numpy(arr, binary_data=True)
    return inp


def numpy_input(name: str, arr: np.ndarray, dtype: str) -> httpclient.InferInput:
    """Numeric tensor (FP32/INT32/UINT8/…)."""
    inp = httpclient.InferInput(name, arr.shape, dtype)
    inp.set_data_from_numpy(arr, binary_data=True)
    return inp