#!/usr/bin/env python3
"""ATD-FX-001 — Threshold Prism Bleed.

Stylized threshold-light compositor for A Thousand Doors.

Truth claim: inspired by real optical behaviors (diffraction/spreading at edges,
scattering, wavelength separation, and aperture-geometry-dependent patterns),
but this is deliberately NOT a physically exact wave-optics simulation.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class ThresholdPrismParams:
    intensity: float = 0.75
    chroma_shift_px: int = 8
    bloom_sigma: float = 8.0
    ray_count: int = 18
    ghost_opacity: float = 0.13


def apply_threshold_prism_bleed(
    frame_bgr: np.ndarray,
    threshold_rect: tuple[int, int, int, int],
    time_seconds: float,
    params: ThresholdPrismParams = ThresholdPrismParams(),
    ghost_room: np.ndarray | None = None,
) -> np.ndarray:
    """Composite localized spectral edge bleed, bloom, rays, and ghost exposure.

    The effect is constrained to a door/threshold edge mask. It intentionally
    avoids a full-frame rainbow wash. `ghost_room`, when supplied, is visible
    only inside the threshold opening.
    """
    img = frame_bgr.astype(np.float32)
    h, w = frame_bgr.shape[:2]
    x1, y1, x2, y2 = [int(v) for v in threshold_rect]
    x1, x2 = sorted((max(0, x1), min(w - 1, x2)))
    y1, y2 = sorted((max(0, y1), min(h - 1, y2)))
    p = float(np.clip(params.intensity, 0.0, 1.0))
    if p <= 0.0 or x2 <= x1 or y2 <= y1:
        return frame_bgr.copy()

    edge = np.zeros((h, w), np.uint8)
    thickness = max(2, int(3 + 8 * p))
    cv2.rectangle(edge, (x1, y1), (x2, y2), 255, thickness)
    opening = np.zeros((h, w), np.uint8)
    cv2.rectangle(opening, (x1 + 2, y1 + 2), (x2 - 2, y2 - 2), 255, -1)

    edge_f = cv2.GaussianBlur(
        edge, (0, 0), max(1.0, params.bloom_sigma * (0.45 + 0.55 * p))
    ).astype(np.float32) / 255.0

    spectral = np.zeros_like(img)
    shift = max(1, int(params.chroma_shift_px * p))
    spectral[..., 2] = np.roll(edge_f, shift, axis=1) * 210.0
    spectral[..., 1] = edge_f * 145.0
    spectral[..., 0] = np.roll(edge_f, -shift, axis=1) * 225.0

    core = cv2.GaussianBlur(opening, (0, 0), 3.0 + 7.0 * p).astype(np.float32) / 255.0
    spectral += core[..., None] * np.array([62.0, 92.0, 150.0], np.float32) * p

    rays = np.zeros((h, w), np.float32)
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    for k in range(max(1, params.ray_count)):
        a = k * math.tau / params.ray_count + 0.18 * math.sin(time_seconds * 0.7 + k)
        sx = int(cx + (x2 - x1) * 0.48 * math.cos(a))
        sy = int(cy + (y2 - y1) * 0.48 * math.sin(a))
        length = int((55 + 210 * p) * (0.55 + 0.45 * ((k * 37) % 17) / 16.0))
        ex, ey = int(sx + length * math.cos(a)), int(sy + length * math.sin(a))
        cv2.line(rays, (sx, sy), (ex, ey), 0.12 + 0.22 * p, 1)
    rays = cv2.GaussianBlur(rays, (0, 0), 4.0 + 4.0 * p)
    spectral += rays[..., None] * np.array([90.0, 132.0, 195.0], np.float32) * p

    if ghost_room is not None and p > 0.3:
        ghost = cv2.resize(ghost_room, (w, h)).astype(np.float32)
        alpha = (opening.astype(np.float32) / 255.0)[..., None]
        alpha *= float(params.ghost_opacity) * p
        img = img * (1.0 - alpha) + ghost * alpha

    return np.clip(img + spectral * p, 0, 255).astype(np.uint8)
