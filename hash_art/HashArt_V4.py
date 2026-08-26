from datetime import datetime
from pathlib import Path
import time
import numpy as np
import xxhash
from PIL import Image
from secrets import token_bytes

def get_neighbors(row: int, col: int, height: int, width: int, pixels: np.ndarray):
    ya = (height - 1 if row == 0 else row - 1, row, 0 if row == height - 1 else row + 1)
    xa = (width - 1 if col == 0 else col - 1, col, 0 if col == width - 1 else col + 1)
    return pixels[np.ix_(ya, xa)]

def compare_neighbors(centre: np.ndarray, neighbors: np.ndarray, max_distance: int):
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

def derive_seed(seed_material: str | bytes):
    if isinstance(seed_material, str):
        seed_material = seed_material.encode()
    return xxhash.xxh128(seed_material).digest()

def hash_to_rgb(digest: bytes):
    return np.frombuffer(digest, dtype=np.uint8, count=15).reshape(5, 3).sum(
        axis=0,
        dtype=np.uint8,
    )

def next_hash(prev_hash: bytes, nonce: int):
    return xxhash.xxh128(prev_hash + nonce.to_bytes(8, 'little')).digest()

def mine_pixel(neighbors, prev_hash, max_distance, nonce_start = 1, nonce_step = 1):
    relaxation = 0
    nonce = nonce_start
    new_hash = next_hash(prev_hash, nonce)
    centre = hash_to_rgb(new_hash)
    
    while not compare_neighbors(centre, neighbors, max_distance + relaxation):
        nonce += nonce_step
        new_hash = next_hash(prev_hash, nonce)
        centre = hash_to_rgb(new_hash)
        # gradually expands acceptable area with each fail to prevent infinite loops
        # as two neighbors might be far apart enough that their acceptance radii don't overlap
        relaxation += 1 
        
    return new_hash, centre

def start_prompt(brief: str):
    print(f"Pre Mining Brief\n{brief}")
    try:
        input("Press Enter to begin or Ctrl-C to stop (now or at any time)\n")
    except KeyboardInterrupt:
        exit(0)

def contra_diagonal_traverse(height, width):
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

def mine(height, width, pixels, mined_hash, distance_limits):
    _get_neighbors = get_neighbors
    _mine_pixel = mine_pixel
    
    area = width * height
    report_interval = area // 10
    
    for i, (row, col) in enumerate(contra_diagonal_traverse(height, width)):
        max_distance = distance_limits[row, col]
        neighbors = _get_neighbors(row, col, height, width, pixels)
        mined_hash, rgb = _mine_pixel(
            neighbors=neighbors, 
            prev_hash=mined_hash, 
            max_distance=max_distance
        )
        pixels[row, col] = rgb
        
        if i % report_interval == 0:
            print(f'{i:,}/{area:,} {row / area:0.2%}')

def save_output(et: float, size: tuple[int, int], initial_hash: bytes, brief: str, review: str, pixels: np.ndarray):
    script_path = Path(__file__)
    
    # format timestamps
    generation_time = datetime.fromtimestamp(et)
    file_timestamp = generation_time.strftime("%Y%m%d_%H%M%S")
    
    # format label
    title_string = f"{file_timestamp}_hash_art_sync_v3.1_{initial_hash.hex()}"
    
    img = Image.fromarray(pixels, 'RGB').resize(size, Image.Resampling.NEAREST)  

    out_path = script_path.parent / 'Generated Images' / f"{title_string}.jpg"
    out_path.parent.mkdir(exist_ok=True)

    img.save(out_path, "jpeg", quality=85)
    
    print(f"Mined image has been saved to disk at: {out_path}")
    img.show()

def main(scale = 4, width = 1080, height = 1080, sigma = 50):
    scaled_width, scaled_height = width // scale, height // scale
        
    initial_hash = derive_seed(token_bytes(32))
    
    rng = np.random.default_rng(seed=int.from_bytes(initial_hash, 'little'))
    distance_limits = rng.exponential(2 * sigma ** 2, (scaled_height, scaled_width)).astype(np.uint32)
    
    pixels = np.zeros((scaled_height, scaled_width, 3), dtype=np.uint8)
    
    brief = (
        f"- Seed hash vein: xxh128[{initial_hash.hex(':')}]\r\n"
        f"- Total being mined: {scaled_height * scaled_width:,d} px\r\n"
        f"- Post mining upscale factor: x{scale}\r\n"
    )
    
    start_prompt(brief)
    st = time.time()
    
    try:
        mine(scaled_height, scaled_width, pixels, initial_hash, distance_limits)
        et = time.time()
        
        review = f'- Time Elapsed: {et - st:.2f}s'
        print(f'Mining complete.\n{review}')
                
        save_output(et, (width, height), initial_hash, brief, review, pixels)
    
    except KeyboardInterrupt:
        et = time.time() 
    
        p = np.mean(np.any(pixels != 0, axis=-1))
        print(f"Mining aborted at {p:.2%} progress\nTime elapsed: {et - st:,.2f}s\nMined image will not be saved to disk.")
    
        Image.fromarray(pixels, 'RGB').show()

if __name__ == '__main__':
    main()