import time

import numpy as np
import xxhash
from PIL import Image, ImageFilter
from secrets import token_bytes

def get_neighbors(row: int, col: int, height: int, width: int, pixels: np.ndarray):
    ya = (height - 1 if row == 0 else row - 1, row, 0 if row == height - 1 else row + 1)
    xa = (width - 1 if col == 0 else col - 1, col, 0 if col == width - 1 else col + 1)
    return pixels[np.ix_(ya, xa)]

def compare_neighbors(
    centre: np.ndarray,
    neighbors: np.ndarray,
    max_distance: int,
):
    mask = np.any(neighbors != 0, axis=-1)
    
    if not np.any(mask):
        return True

    delta = np.subtract(
        neighbors[mask],
        centre,
        dtype=np.int32,
    )
    np.multiply(delta, delta, out=delta)
    distances = np.sum(delta, axis=-1)

    return bool(np.all(distances <= max_distance))

RGB_MODULUS = 256

def derive_seed(seed_material: str | bytes) -> bytes:
    if isinstance(seed_material, str):
        seed_material = seed_material.encode()
    return xxhash.xxh128(seed_material).digest()

def hash_to_rgb(digest: bytes) -> np.ndarray:
    return np.frombuffer(digest, dtype=np.uint8, count=15).reshape(5, 3).sum(
        axis=0,
        dtype=np.uint8,
    )

def next_hash(prev_hash: bytes, nonce: int) -> bytes:
    """Next chain link: xxh128(prev_hash || str(nonce))."""
    return xxhash.xxh128(prev_hash + nonce.to_bytes(8)).digest()

def mine_pixel(
    neighbors: np.ndarray, prev_hash: bytes, max_distance: float, nonce_start: int = 1, nonce_step: int = 1
) -> tuple[bytes, np.ndarray]:
    """
    Search nonces until the example neighbor rule accepts a color.
    Interleaved to improve async efficiency
    """
    nonce = nonce_start
    new_hash = next_hash(prev_hash, nonce)
    centre = hash_to_rgb(new_hash)
    
    while not compare_neighbors(centre, neighbors, max_distance):
        nonce += nonce_step
        new_hash = next_hash(prev_hash, nonce)
        centre = hash_to_rgb(new_hash)
        
    return new_hash, centre

if __name__ == '__main__':
    SCALE = 8
    WIDTH = 1_080 #1_920
    HEIGHT = 1_080
    SIGMA = 25 # 50 is a good middleground for Speed vs LoD
    
    width, height = 1_920 // SCALE, 1_080 // SCALE
    
    mined_hash = derive_seed(token_bytes(32))
    
    print(f'Starting Hash: xxh128:{mined_hash.hex(':')}')
    
    rng = np.random.default_rng(seed=int.from_bytes(mined_hash))
    distance_limits = rng.exponential(2 * SIGMA ** 2, (height, width)).astype(np.int32)
    
    pixels = np.zeros([height, width, 3], dtype=np.uint8)
    
    st = time.time()
    for row in range(height):
        for col in range(width):
            max_distance = distance_limits[row, col]
            neighbors = get_neighbors(row, col, height, width, pixels)
            mined_hash, rgb = mine_pixel(neighbors, mined_hash, max_distance)
            pixels[row, col] = rgb
        print(f'{row}/{height} {row / height:0.1%}')
    
    et = time.time() 
    print(f'Finished Mining.\nTime Elapsed: {et - st:0.2f}s')
            
    img = Image.fromarray(pixels, 'RGB')
    img = img.resize((WIDTH, HEIGHT), Image.Resampling.NEAREST)
    img = img.filter(ImageFilter.GaussianBlur(1.0))
    img.save('./Generated Images/hash_art_v3.png')
    img.show()