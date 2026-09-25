import math
import unicodedata
import colorsys
from PIL import Image, ImageDraw

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

def evaluate_palette(hsv1, hsv2, hsv3):
    """
    Evaluates palette aesthetic quality.
    Returns: 
      0: AESTHETICALLY BALANCED
      1: Vibrating/Clashing Colors
      2: Muddy/Flat Palette
      3: Poor Harmony / Accidental Angles
    """
    colors = [hsv1, hsv2, hsv3]
    hues = sorted([c[0] for c in colors])
    sats = [c[1] for c in colors]
    vals = [c[2] for c in colors]
    
    # 1. Test for Vibrating/Clashing Colors
    pairs = [(0, 1), (1, 2), (0, 2)]
    for i, j in pairs:
        dh = min(abs(colors[i][0] - colors[j][0]), 360 - abs(colors[i][0] - colors[j][0]))
        if dh > 150 and colors[i][1] > 0.8 and colors[j][1] > 0.8 and colors[i][2] > 0.8 and colors[j][2] > 0.8:
            return 1

    # 2. Test for Muddy / Lack of Dynamic Range
    mean_s = sum(sats) / 3
    mean_v = sum(vals) / 3
    std_s = math.sqrt(sum((s - mean_s) ** 2 for s in sats) / 3)
    std_v = math.sqrt(sum((v - mean_v) ** 2 for v in vals) / 3)
    
    if std_s < 0.12 and std_v < 0.12:
        return 2

    # 3. Test for Uncanny Color Harmony Angles
    d1 = hues[1] - hues[0]
    d2 = hues[2] - hues[1]
    d3 = 360 - (hues[2] - hues[0])
    intervals = sorted([d1, d2, d3])
    
    is_analogous = (intervals[0] + intervals[1]) < 65
    is_triadic = (95 <= intervals[0] <= 145) and (95 <= intervals[1] <= 145)
    is_split_comp = (intervals[0] < 45) and (135 <= intervals[1] <= 180)
    
    if not (is_analogous or is_triadic or is_split_comp):
        return 3
        
    return 0

def generate_colours(dec_hash):
    """
    Generates a high-quality 3-color palette from a 30-bit decimal hash.
    Rotates the hash up to 30 times to clear collision errors.
    Procedurally tweaks values as a secondary fallback strategy.
    """
    best_palette = None
    best_score = float('inf')
    
    # Mask to keep the hash strictly bound to 30 bits during bitwise rotation
    HASH_MASK = (1 << 30) - 1 

    # --- STRATEGY 1: Rotate the 30-bit hash to find an ideal seed ---
    for rotation in range(30):
        # Perform a bitwise circular rotation using the 30-bit limits
        current_hash = ((dec_hash >> rotation) | (dec_hash << (30 - rotation))) & HASH_MASK
        
        # Extract base normalized RGB from the 24-bit window
        rgb = [
            ((current_hash >> n) & HEX_BASE) / HEX_BASE 
            for n in range(0, WHITE_HEX_BITS, HEX_BITS)
        ]
        
        base_hsv = colorsys.rgb_to_hsv(*rgb)
        
        # Build the triad array out of HSV structures first to evaluate them
        hsv_triad = []
        for n in range(0, 7, 3):
            # Map standard 0.0-1.0 hue format up to 360 degrees for evaluation script
            h_deg = ((base_hsv[0] + 0.11 * n) % 1.0) * 360.0
            hsv_triad.append((h_deg, base_hsv[1], base_hsv[2]))
        
        score = evaluate_palette(hsv_triad[0], hsv_triad[1], hsv_triad[2])
        
        # Exact structural fit found! Convert directly to 8-bit RGB integers
        if score == 0:
            return [
                tuple(int(c * 255) for c in colorsys.hsv_to_rgb((h[0]/360.0), h[1], h[2]))
                for h in hsv_triad
            ]
        
        # Cache the lowest error score found across all 30 rotations
        if score < best_score:
            best_score = score
            best_palette = hsv_triad

    # --- STRATEGY 2: Procedural Tweak Fallback ---
    # If a score of 0 wasn't achieved via raw hashes, fix the best available palette
    tweaked_palette = []
    
    for idx, (h, s, v) in enumerate(best_palette):
        # Fix Error 1 (Vibrating): Systematically step down saturation/brightness on secondary items
        if best_score == 1 and idx > 0:
            s = max(0.0, s - 0.25)
            v = max(0.0, v - 0.15)
            
        # Fix Error 2 (Muddy): Introduce systematic, uneven value offsets to force dynamic range
        elif best_score == 2:
            if idx == 0:   v = min(1.0, v + 0.20)  # Lighten base
            elif idx == 2: v = max(0.0, v - 0.20)  # Darken accent
            
        # Note: Error 3 (Accidental Angles) cannot be dynamically fixed without rewriting the hue logic,
        # but returning the best-scoring rotation minimizes the clashing impact.
        
        tweaked_palette.append((h, s, v))
        
    # Translate the final optimized HSV structural variables back into integer 8-bit RGB pairs
    return [
        tuple(int(c * 255) for c in colorsys.hsv_to_rgb((item[0] / 360.0), item[1], item[2]))
        for item in tweaked_palette
    ]

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