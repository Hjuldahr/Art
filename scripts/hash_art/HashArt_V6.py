from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import xxhash
from secrets import token_bytes

def polar_color_to_HSX(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    # 1. Calculate Hue and normalize to standard [0, 360] range
    h = np.arctan2(b, a)
    np.rad2deg(h, out=h)
    h %= 360.0 
    
    # Normalize to a 0-1 range for a circular boundary
    rho = np.hypot(a, b) / np.sqrt(2.0)
    np.clip(rho, 0.0, 1.0, out=rho)
    
    # X is used as it can mean either lightness or value since its coming from a custom colour space
    x = 0.5 + 0.5 * np.cos(rho * np.pi) 
    s = np.sin(rho * np.pi) 
    
    return np.dstack((h, s, x))

def get_neighbors(row: int, col: int, height: int, width: int, pixels: np.ndarray):
    ya = (height - 1 if row == 0 else row - 1, row, 0 if row == height - 1 else row + 1)
    xa = (width - 1 if col == 0 else col - 1, col, 0 if col == width - 1 else col + 1)
    return pixels[np.ix_(ya, xa)]

def compare_neighbors(centre: np.ndarray, neighbors: np.ndarray, max_distance: int):
    mask = ~np.isnan(neighbors)
    if not np.any(mask):
        return True
    
    distances = np.subtract(neighbors[mask], centre)
    np.absolute(distances, out=distances)
    
    return bool(np.all(distances <= max_distance))

def derive_seed(seed_material: str | bytes) -> bytes:
    if isinstance(seed_material, str):
        seed_material = seed_material.encode()
        
    return xxhash.xxh128(seed_material).digest()

def next_hash(prev_hash: bytes, nonce: int) -> bytes:
    """Next chain link: xxh128(prev_hash || str(nonce))."""
    return xxhash.xxh128(prev_hash + nonce.to_bytes(8)).digest()

def hash_to_chx(digest: bytes) -> np.ndarray:
    hash_int = int.from_bytes(digest, byteorder='little')
    normalized_0_1 = float(hash_int) / (2**128 - 1)
    return np.float64(normalized_0_1 * 2.0 - 1.0)

def mine_pixel(
    neighbors: np.ndarray, prev_hash: bytes, max_distance: float, nonce_start: int = 1, nonce_step: int = 1
) -> tuple[bytes, np.ndarray]:
    """
    Search nonces until the example neighbor rule accepts a color.
    """
    relaxation = 0
    nonce = nonce_start
    new_hash = next_hash(prev_hash, nonce)
    centre = hash_to_chx(new_hash)
    
    while not compare_neighbors(centre, neighbors, max_distance + relaxation):
        nonce += nonce_step
        new_hash = next_hash(prev_hash, nonce)
        centre = hash_to_chx(new_hash)
        # gradually expands acceptable area with each fail to prevent infinite loops
        # as two neighbors might be far apart enough that their acceptance radii don't overlap
        relaxation += 1 
        
    return new_hash, centre

def apply_bloom(original, radius=20, brightness_boost=1.5, blend_alpha=0.4):
    # 1. Open original image
    # 2. Increase contrast/brightness to isolate highlights (bright pass)
    enhancer = ImageEnhance.Brightness(original)
    highlights = enhancer.enhance(brightness_boost)
    
    # 3. Apply Gaussian blur to create the soft glow
    glow = highlights.filter(ImageFilter.GaussianBlur(radius))
    
    # 4. Blend the glow back onto the original image using additive/alpha blend
    bloomed_image = Image.blend(original, glow, blend_alpha)
    
    return bloomed_image

def save_output(size: tuple[int, int], initial_seed: bytes, pixels: np.ndarray):
    script_path = Path(__file__)
    
    img = Image.fromarray(pixels, 'HSV').convert('RGB').resize(size, Image.Resampling.NEAREST)  
    
    generation_time = datetime.now(timezone.utc)
    file_timestamp = generation_time.strftime("%Y%m%d_%H%M%S")
    title_string = f"{file_timestamp}_hash_art_v6_{initial_seed.hex()}"
    
    out_path = script_path.parent / 'Generated Images' / f"{title_string}.jpg"
    out_path.parent.mkdir(exist_ok=True)

    apply_bloom(img, radius=10, brightness_boost=1.0).save(out_path, "jpeg", quality=85)
    
    print(f"Mined image has been saved to disk at: {out_path}")
    img.show()

if __name__ == '__main__':
    SCALE = 4
    WIDTH = 1_080
    HEIGHT = 1_080
    
    width, height = WIDTH // SCALE, HEIGHT // SCALE
    
    initial_seed = derive_seed(token_bytes(32))
    mined_hash_a = initial_seed
    mined_hash_b = initial_seed
    
    rng = np.random.default_rng(seed=int.from_bytes(initial_seed))
    # because values range -1 to 1, the span is 2
    distance_limits = rng.uniform(0.01, 0.125, (height, width))
    
    arr_a = np.full((height, width), np.nan, dtype=np.float64)
    arr_b = np.full((height, width), np.nan, dtype=np.float64)
    
    for p in range(0, height, 2):
        for q in range(width):
            max_distance_a = distance_limits[p, q]
            neighbors_a = get_neighbors(p, q, height, width, arr_a)
            
            max_distance_b = distance_limits[q, p]
            neighbors_b = get_neighbors(q, p, height, width, arr_b)
            
            mined_hash_a, a = mine_pixel(neighbors=neighbors_a, prev_hash=mined_hash_a, max_distance=max_distance_a)
            mined_hash_b, b = mine_pixel(neighbors=neighbors_b, prev_hash=mined_hash_b, max_distance=max_distance_b)
            
            arr_a[p, q] = a
            arr_b[q, p] = b
            
        for q in range(width-1, -1, -1):
            max_distance_b = distance_limits[p+1, q]
            neighbors_b = get_neighbors(p+1, q, height, width, arr_a)
            
            max_distance_a = distance_limits[q, p+1]
            neighbors_a = get_neighbors(q, p+1, height, width, arr_b)
            
            mined_hash_b, b = mine_pixel(neighbors=neighbors_b, prev_hash=mined_hash_b, max_distance=max_distance_b)
            mined_hash_a, a = mine_pixel(neighbors=neighbors_a, prev_hash=mined_hash_a, max_distance=max_distance_a)
            
            arr_b[p+1, q] = b
            arr_a[q, p+1] = a
            
        #print(f'{p}/{q} {p / height:0.1%}')
    
    hsx = polar_color_to_HSX(arr_a, arr_b)
    
    multipliers = np.array([255.0 / 360.0, 255.0, 255.0])
    pixels = (hsx * multipliers).astype(np.uint8)
        
    save_output((WIDTH, HEIGHT), initial_seed, pixels)