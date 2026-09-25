from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import xxhash
from PIL import Image
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
    mask = neighbors != 0
    
    if not np.any(mask):
        return True

    delta = np.subtract(
        neighbors[mask],
        centre,
        dtype=np.int16
    )
    distances = np.abs(delta)

    return bool(np.all(distances <= max_distance))

RGB_MODULUS = 256

def derive_seed(seed_material: str | bytes) -> bytes:
    if isinstance(seed_material, str):
        seed_material = seed_material.encode()
    return xxhash.xxh128(seed_material).digest()

def hash_to_v(digest: bytes, offset=0) -> np.ndarray:
    return np.frombuffer(digest, dtype=np.uint8, count=5, offset=offset).sum(dtype=np.uint8)

def next_hash(prev_hash: bytes, nonce: int) -> bytes:
    """Next chain link: xxh128(prev_hash || str(nonce))."""
    return xxhash.xxh128(prev_hash + nonce.to_bytes(8)).digest()

def mine_pixel(
    neighbors: np.ndarray, prev_hash: bytes, max_distance: float, nonce_start: int = 1, nonce_step: int = 1, offset=0
) -> tuple[bytes, np.ndarray]:
    """
    Search nonces until the example neighbor rule accepts a color.
    """
    relaxation = 0
    nonce = nonce_start
    new_hash = next_hash(prev_hash, nonce)
    centre = hash_to_v(new_hash, offset)
    
    while not compare_neighbors(centre, neighbors, max_distance + relaxation):
        nonce += nonce_step
        new_hash = next_hash(prev_hash, nonce)
        centre = hash_to_v(new_hash, offset)
        # gradually expands acceptable area with each fail to prevent infinite loops
        # as two neighbors might be far apart enough that their acceptance radii don't overlap
        relaxation += 1 
        
    return new_hash, centre, nonce

def save_output(size: tuple[int, int], initial_seed: bytes, pixels: np.ndarray):
    script_path = Path(__file__)
    
    # format timestamps
    generation_time = datetime.now(timezone.utc)
    file_timestamp = generation_time.strftime("%Y%m%d_%H%M%S")
    
    # format label
    title_string = f"{file_timestamp}_hash_art_v5_{initial_seed.hex()}"
    
    img = Image.fromarray(pixels, 'RGB').resize(size, Image.Resampling.NEAREST)  

    out_path = script_path.parent / 'Generated Images' / f"{title_string}.jpg"
    out_path.parent.mkdir(exist_ok=True)

    img.save(out_path, "jpeg", quality=85)
    
    print(f"Mined image has been saved to disk at: {out_path}")
    img.show()

def contra_diagonal_traverse(width, height):
    num_diagonals = width + height - 1
    
    for d in range(num_diagonals):
        # Even diagonals: Sweep DOWN and LEFT
        if d % 2 == 0:
            # Row starts at 0, unless d exceeds the available column indices
            r = 0 if d < width else d - width + 1
            # Column starts at d, but cannot exceed the maximum width index
            c = d if d < width else width - 1
            
            # Bound checking must look at both constraints simultaneously
            while r < height and c >= 0:
                yield r, c
                r += 1
                c -= 1
                
        # Odd diagonals: Sweep UP and RIGHT
        else:
            # Row starts at d, but cannot exceed the maximum height index
            r = d if d < height else height - 1
            # Column starts at 0, unless d exceeds the available row indices
            c = 0 if d < height else d - height + 1
            
            # Bound checking must look at both constraints simultaneously
            while r >= 0 and c < width:
                yield r, c
                r -= 1
                c += 1

def z_traverse(width, height, *, col_first=False):
    if not col_first:
        for row in range(0, height, 2):
            for col in range(width):
                yield row, col
            
            if row + 1 < height:
                for col in range(width - 1, -1, -1):
                    yield row + 1, col
    else:
        for col in range(0, width, 2):
            for row in range(height):
                yield row, col
            
            if col + 1 < width:
                for row in range(height - 1, -1, -1):
                    yield row, col + 1

if __name__ == '__main__':
    SCALE = 4
    WIDTH = 1_080 #1_920
    HEIGHT = 1_080
    SIGMA = 25
    
    width, height = WIDTH // SCALE, HEIGHT // SCALE
        
    initial_seed = derive_seed(token_bytes(32))
    r_mined_hash = initial_seed  # Keep track of running hash variations
    g_mined_hash = initial_seed
    b_mined_hash = initial_seed
    
    rng = np.random.default_rng(seed=int.from_bytes(initial_seed))
    distance_limits = rng.triangular(0, 85, 255, (height, width)).astype(np.uint8)
    
    r_pixels = np.zeros((height, width), dtype=np.uint8)
    g_pixels = np.zeros((height, width), dtype=np.uint8)
    b_pixels = np.zeros((height, width), dtype=np.uint8)
    
    for row, col in z_traverse(width, height):
        max_distance = distance_limits[row, col]
        neighbors = get_neighbors(row, col, height, width, r_pixels)
        r_mined_hash, r, nonces = mine_pixel(
            neighbors=neighbors, 
            prev_hash=r_mined_hash, 
            max_distance=max_distance,
            offset=0
        )
        r_pixels[row, col] = r
    
    for row, col in contra_diagonal_traverse(width, height):
        max_distance = distance_limits[row, col]
        neighbors = get_neighbors(row, col, height, width, g_pixels)
        g_mined_hash, g, nonces = mine_pixel(
            neighbors=neighbors, 
            prev_hash=g_mined_hash, 
            max_distance=max_distance,
            offset=5
        )
        g_pixels[row, col] = g
        
    for row, col in z_traverse(width, height, col_first=True):
        max_distance = distance_limits[row, col]
        neighbors = get_neighbors(row, col, height, width, b_pixels)
        b_mined_hash, b, nonces = mine_pixel(
            neighbors=neighbors, 
            prev_hash=b_mined_hash, 
            max_distance=max_distance,
            offset=0
        )
        b_pixels[row, col] = b
            
    pixels = np.dstack((r_pixels, g_pixels, b_pixels))
                
    save_output((WIDTH, HEIGHT), initial_seed, pixels)