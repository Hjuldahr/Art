import os
import math
import numpy as np
from PIL import Image
import matplotlib.colors as mplcolors
from perlin_noise import PerlinNoise

noise_gen = PerlinNoise(octaves=3)

# --- Config ---
SOURCE_DIR = 'Source Images'
OUTPUT_DIR = 'Generated Images'
THRESHOLD = 10        # degrees of hue difference
SAT_WEIGHT = 0.28
VAL_WEIGHT = 0.72
USE_NOISY_ANGLE = True
USE_RADIAL_SORT = False
USE_DOUBLE_PASS = True
NOISE_SCALE = 0.03    # Smaller = more turbulence
ANGLE_NOISE_MAG = 90  # How far angles can deviate
# ----------------

def hsv_to_rgb_np(hsv_array):
    """Convert HSV array [H 0–360, S,V 0–100] to RGB 0–255."""
    hsv_norm = hsv_array.copy()
    hsv_norm[..., 0] /= 360.0
    hsv_norm[..., 1:] /= 100.0
    rgb = mplcolors.hsv_to_rgb(hsv_norm)
    return (rgb * 255).astype(np.uint8)

def rgb_to_hsv_np(rgb_array):
    """Convert RGB array [0–255] to HSV [H 0–360, S,V 0–100]."""
    rgb_norm = rgb_array / 255.0
    hsv = mplcolors.rgb_to_hsv(rgb_norm)
    hsv[..., 0] *= 360.0
    hsv[..., 1:] *= 100.0
    return hsv

def get_theta(h_start, x, y):
    if USE_NOISY_ANGLE:
        angle_noise = noise_gen([x / width, y / height]) * ANGLE_NOISE_MAG
        return np.deg2rad((h_start + angle_noise) % 360)
    return np.deg2rad(h_start)

def bresenham_line_threshold(x0, y0, width, height, hsv_pixels, hue_threshold):
    points, colors = [], []
    h_start = hsv_pixels[y0, x0, 0]

    theta_rad = get_theta(h_start, x0, y0)
    dx = int(np.cos(theta_rad) * width)
    dy = int(np.sin(theta_rad) * height)

    x, y = x0, y0
    sx = 1 if dx > 0 else -1
    sy = 1 if dy > 0 else -1
    dx, dy = abs(dx), abs(dy)
    
    # Early escape for degenerate lines (single pixel)
    if dx == dy == 0:
        return [], np.empty((0, 3))
    
    err = dx - dy

    # Longest possible line length is the diagonal of a rectangle (worst case scenario in terms of valid travel distance)
    # Algorithm in most cases will escape early but it prevents infinite loops
    for _ in range(int(math.hypot(width, height)) + 1):
        if not (0 <= x < width and 0 <= y < height):
            break
        hue = hsv_pixels[y, x, 0]
        value = hsv_pixels[y, x, 2]
        # Gets normalized angle difference between hues 
        hue_diff = abs((h_start - hue) % 360)
        # Gets smallest angle to zero (315 -> 45, 45 -> 45)
        hue_diff = min(hue_diff, 360 - hue_diff)
        # If the angle of the hue exceeds the threshold in either direction or the colour is nearly black (value = 0)
        if hue_diff > hue_threshold or value < 2:
            break
        points.append((x, y))
        colors.append(hsv_pixels[y, x])
        if x == x0 + dx and y == y0 + dy:
            break
        e2 = err * 2
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy

    return points, np.array(colors)

def sortAlongBresenham(hsv_pixels, x, y, width, height, sat_weight, val_weight, threshold):
    if hsv_pixels[y, x, 2] < 2:
        return hsv_pixels
    points, colors = bresenham_line_threshold(x, y, width, height, hsv_pixels, threshold)
    if len(points) > 1:
        sort_scores = sat_weight * colors[:, 1] + val_weight * colors[:, 2]
        sorted_indices = np.argsort(sort_scores)
        sorted_colors = colors[sorted_indices]
        for (px, py), color in zip(points, sorted_colors):
            hsv_pixels[py, px] = color
    return hsv_pixels

def apply_pixel_sort(hsv_pixels, width, height):
    if USE_RADIAL_SORT:
        cx, cy = width // 2, height // 2
        coords = sorted([(x, y) for x in range(width) for y in range(height)],
                        key=lambda p: math.hypot(p[0] - cx, p[1] - cy))
    else:
        coords = [(x, y) for y in range(height) for x in range(width)]

    for i, (x, y) in enumerate(coords):
        if i % 1000 == 0:
            print(f"Progress: {i}/{len(coords)} ({i / len(coords):.2%})", end="\r")
        hsv_pixels = sortAlongBresenham(hsv_pixels, x, y, width, height, SAT_WEIGHT, VAL_WEIGHT, THRESHOLD)

    return hsv_pixels

# -------------------------------
# Main Script
# -------------------------------
parent_dir = os.path.dirname(__file__)
source_dir = os.path.join(parent_dir, SOURCE_DIR)
output_dir = os.path.join(parent_dir, OUTPUT_DIR)
os.makedirs(output_dir, exist_ok=True)

file_names = os.listdir(source_dir)
print(f"Processing {len(file_names)} images...\n")

for number, file_name in enumerate(file_names, start=1):
    print(f"\nProcessing {file_name} [{number}/{len(file_names)}]")
    image_path = os.path.join(source_dir, file_name)
    image = Image.open(image_path).convert("RGB")
    rgb_pixels = np.array(image)
    height, width = rgb_pixels.shape[:2]

    hsv_pixels = rgb_to_hsv_np(rgb_pixels)
    hsv_pixels = apply_pixel_sort(hsv_pixels, width, height)

    if USE_DOUBLE_PASS:
        print("\nStarting pass 2 (rotated)...")
        hsv_pixels = np.rot90(hsv_pixels, 1)
        hsv_pixels = apply_pixel_sort(hsv_pixels, height, width)
        hsv_pixels = np.rot90(hsv_pixels, -1)

    rgb_sorted = hsv_to_rgb_np(hsv_pixels)
    output_path = os.path.join(output_dir, f'PXLS7-{number}_{file_name}')
    Image.fromarray(rgb_sorted).save(output_path)
    print(f"Saved to {output_path}")

print("\nCompleted!")