import math
import unicodedata
import colorsys
from PIL import Image, ImageDraw, ImageFilter

BIT_LENGTH = 12
HEX_BASE = 0xFF  
HASH_BITS = 30    
HEX_BITS = 8  

WHITE_HEX_BITS = 24

def generate_asymmetric_map() -> list:
    seen_rotations = set()
    canonical_representatives = []
    
    for i in range(1 << BIT_LENGTH):
        binary_str = f"{i:0{BIT_LENGTH}b}"
        rotations = [binary_str[k:] + binary_str[:k] for k in range(BIT_LENGTH)]
        min_rotation = min(rotations)
        
        if min_rotation not in seen_rotations:
            seen_rotations.add(min_rotation)
            canonical_representatives.append(min_rotation)
            
        if len(canonical_representatives) == HEX_BASE + 1:
            break
            
    return canonical_representatives

LOOKUP = generate_asymmetric_map()

CIRCLE = 360
CIRCLE_INTERVAL = CIRCLE / BIT_LENGTH

def fractions():
    fractions = []
    for i in range(BIT_LENGTH):
        v = CIRCLE_INTERVAL * i
        fractions.append({
            'start': v,
            'end': v + CIRCLE_INTERVAL
        })
    return fractions
        
FRACTIONS = fractions()

def compute_utf8_hash(s: str) -> int:
    normalized_str = unicodedata.normalize('NFC', s)
    utf8_bytes = normalized_str.encode('utf-8')

    p = 257 
    m = 10**9 + 9
    hash_value = 0
    p_power = 1
    
    for byte in utf8_bytes:
        byte_val = byte + 1
        hash_value = (hash_value + byte_val * p_power) % m
        p_power = (p_power * p) % m
        
    return hash_value

def draw(drawing: ImageDraw.ImageDraw, value: str, fill: tuple, bg: tuple, center: tuple, inner_radius: float, outer_radius: float):
    x, y = center
    xy_outer = ((x - outer_radius, y - outer_radius), (x + outer_radius, y + outer_radius))
    
    for n in range(BIT_LENGTH):
        if value[n] == '1':
            drawing.pieslice(xy_outer, fill=fill, **FRACTIONS[n])
        
    if inner_radius > 0:
        xy_inner = ((x - inner_radius, y - inner_radius), (x + inner_radius, y + inner_radius))    
        drawing.ellipse(xy_inner, fill=bg)

def evaluate_pallete(hsv1, hsv2, hsv3):
    colors = [hsv1, hsv2, hsv3]
    hues = sorted([c[0] for c in colors])
    sats = [c[1] for c in colors]
    vals = [c[2] for c in colors]
    
    # 1. Test for Vibrating/Clashing Colors
    pairs = [(0, 1), (1, 2), (0, 2)]
    for i, j in pairs:
        dh = min(abs(colors[i][0] - colors[j][0]), 360 - abs(colors[i][0] - colors[j][0]))
        if dh > 150 and colors[i][1] > 0.8 and colors[j][1] > 0.8 and colors[i][2] > 0.8 and colors[j][2] > 0.8:
            return 1 #"AESTHETIC FAILURE: Colors vibrate violently (e.g., raw neon red next to raw neon cyan)."

    # 2. Test for Muddy / Lack of Dynamic Range
    mean_s = sum(sats) / 3
    mean_v = sum(vals) / 3
    std_s = math.sqrt(sum((s - mean_s) ** 2 for s in sats) / 3)
    std_v = math.sqrt(sum((v - mean_v) ** 2 for v in vals) / 3)
    
    if std_s < 0.12 and std_v < 0.12:
        return 2 #"AESTHETIC FAILURE: Muddy/Flat palette. All three colors have identical weight, saturation, and lightness."

    # 3. Test for Uncanny Color Harmony Angles
    d1 = hues[1] - hues[0]
    d2 = hues[2] - hues[1]
    d3 = 360 - (hues[2] - hues[0])
    intervals = sorted([d1, d2, d3]) # Smallest to largest gaps
    
    # Check if it fails classic architectural shapes
    is_analogous = (intervals[0] + intervals[1]) < 65
    is_triadic = (100 <= intervals[0] <= 140) and (100 <= intervals[1] <= 140)
    is_split_comp = (intervals[0] < 45) and (135 <= intervals[1] <= 180)
    
    if not (is_analogous or is_triadic or is_split_comp):
        return 3 #"POOR HARMONY: The hue intervals look accidental. They miss classic pleasing geometric harmonies."
        
    return 0 #"AESTHETICALLY BALANCED: Good variance in tones, shapes, or structural contrast."

def generate_colours(dec_hash):
    rgb = [
        ((dec_hash >> n) & HEX_BASE) / HEX_BASE 
        for n in range(0, WHITE_HEX_BITS, HEX_BITS)
    ]
    
    hsv = colorsys.rgb_to_hsv(*rgb)

    rotated_rgb = [
        tuple(
            int(c * 255) for c in k
        ) for k in (
            colorsys.hsv_to_rgb((hsv[0] + 0.11 * n) % 1.0, hsv[1], hsv[2]) 
            for n in range(0, 7, 3)
        )
    ]
    
    return rotated_rgb 

# Input configuration
text = 'Hjuldahr'

dec_hash = compute_utf8_hash(text)

colours = generate_colours(dec_hash)

hex_hash = [(dec_hash >> n) & HEX_BASE for n in range(0, HASH_BITS, HEX_BITS)]
hex_hash = [LOOKUP[xh] for xh in hex_hash]

# TARGET SIZE
target_w, target_h = 256, 256
padding_target = 3  

# SUPERSAMPLING MULTIPLIER (4x renders at 1024x1024 internally)
SCALE = 4
img_w, img_h = target_w * SCALE, target_h * SCALE
padding = padding_target * SCALE

center = (img_w / 2, img_h / 2)
radius = min(center)
radius_increments = radius / len(hex_hash)

# Render canvas at high-res
canvas = Image.new("RGB", (img_w, img_h), colours[0])
drawing = ImageDraw.Draw(canvas)

for i in range(len(hex_hash) - 1, -1, -1):
    xh = hex_hash[i]
    fill = colours[(i % 2) + 1]  
    
    channel_start = radius_increments * i
    channel_end = channel_start + radius_increments
    
    inner_radius = channel_start + padding
    outer_radius = channel_end - padding
    
    draw(drawing, xh, fill, colours[0], center, inner_radius, outer_radius)
    
drawing.circle(center, radius_increments * 0.25, fill=colours[0])

canvas = canvas.resize((target_w, target_h), Image.Resampling.LANCZOS)

canvas.show()