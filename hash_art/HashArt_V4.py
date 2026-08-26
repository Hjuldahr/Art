import datetime
from pathlib import Path
import time
from numba import jit

import numpy as np
import xxhash
from PIL import Image, ExifTags
from secrets import token_bytes

@jit
def get_neighbors(row: int, col: int, height: int, width: int, pixels: np.ndarray):
    ya = (height - 1 if row == 0 else row - 1, row, 0 if row == height - 1 else row + 1)
    xa = (width - 1 if col == 0 else col - 1, col, 0 if col == width - 1 else col + 1)
    return pixels[np.ix_(ya, xa)]

@jit
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

@jit
def hash_to_rgb(digest: bytes) -> np.ndarray:
    return np.frombuffer(digest, dtype=np.uint8, count=15).reshape(5, 3).sum(
        axis=0,
        dtype=np.uint8,
    )

@jit
def next_hash(prev_hash: bytes, nonce: int) -> bytes:
    """Next chain link: xxh128(prev_hash || str(nonce))."""
    return xxhash.xxh128(prev_hash + nonce.to_bytes(8)).digest()

@jit
def mine_pixel(
    neighbors: np.ndarray, prev_hash: bytes, max_distance: float, nonce_start: int = 1, nonce_step: int = 1
) -> tuple[bytes, np.ndarray]:
    """
    Search nonces until the example neighbor rule accepts a color.
    """
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
        
    return new_hash, centre, nonce

def start_prompt(brief: str):
    print(f"Pre Mining Brief\n{brief}")
    try:
        input("Press Enter to begin or Ctrl-C to stop (now or at any time)\n")
    except KeyboardInterrupt:
        exit(0)

def save_output(et: float, size: tuple[int, int], mined_hash: bytes, brief: str, review: str, pixels: np.ndarray):
    script_path = Path(__file__)
    
    # format timestamps
    generation_time = datetime.fromtimestamp(et)
    exif_time_string = generation_time.strftime("%Y:%m:%d %H:%M:%S")
    file_timestamp = generation_time.strftime("%Y%m%d_%H%M%S")
    
    # format label
    title_string = f"{file_timestamp}_hash_art_sync_v3.1_{mined_hash.hex()}"
    description_string = f"{brief}\r\n{review}"
    
    img = Image.fromarray(pixels, 'RGB').resize(size, Image.Resampling.NEAREST)  
            
    # add metadata sugar
    exif_data = img.getexif()
    exif_data[ExifTags.Base.Artist] = "Nioureux"
    exif_data[ExifTags.Base.Software] = script_path.name  
    exif_data[ExifTags.Base.DateTime] = exif_time_string          
    exif_data[ExifTags.Base.DateTimeOriginal] = exif_time_string  
    exif_data[ExifTags.Base.DateTimeDigitized] = exif_time_string 
    exif_data[ExifTags.Base.ImageDescription] = f"{title_string}\r\n{description_string}"
    # Override fields to cleanup representation on windows machines specifically 
    # (uses a split field which looks ugly when duplicated)
    exif_data[ExifTags.Base.XPTitle] = title_string.encode('utf-16le')
    exif_data[ExifTags.Base.XPSubject] = description_string.replace("\r", "").replace("\n", "; ").encode('utf-16le')
    
    out_path = script_path.parent / 'Generated Images' / f"{title_string}.jpg"
    out_path.parent.mkdir(exist_ok=True)

    img.save(out_path, "jpeg", exif=exif_data, quality=85)
    
    print(f"Mined image has been saved to disk at: {out_path}")
    img.show()

@jit
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

@jit
def mine(width, height, pixels, distance_limits):
    _get_neighbors = get_neighbors
    _mine_pixel = mine_pixel
    
    for row, col in contra_diagonal_traverse(width, height):
        max_distance = distance_limits[row, col]
        neighbors = _get_neighbors(row, col, height, width, pixels)
        mined_hash, rgb, nonces = _mine_pixel(
            neighbors=neighbors, 
            prev_hash=mined_hash, 
            max_distance=max_distance
        )
        pixels[row, col] = rgb
        total_nonces += nonces
        
        if row == col:
            print(f'{row}/{height} {row / height:0.1%}')

def main(scale = 4, width = 1080, height = 1080, sigma = 25):
    scaled_width, scaled_height = width // scale, height // scale
        
    initial_seed = derive_seed(token_bytes(32))
    mined_hash = initial_seed  # Keep track of running hash variations
    
    rng = np.random.default_rng(seed=int.from_bytes(initial_seed))
    distance_limits = rng.exponential(2 * sigma ** 2, (height, width)).astype(np.uint32)
    
    pixels = np.zeros((height, width, 3), dtype=np.uint8)
    
    brief = (
        f"- Seed hash vein: xxh128[{initial_seed.hex(':')}]\r\n"
        f"- Total being mined: {height * width:,d} px\r\n"
        f"- Post mining upscale factor: x{scale}\r\n"
    )
    
    start_prompt(brief)
    st = time.time()
    total_nonces = 0
    
    try:
        mine(width, height, pixels, distance_limits)
        et = time.time()
        
        review = f'- Time Elapsed: {et - st:.2f}s\r\n- Nonces Searched: {total_nonces:,d}'
        print(f'Mining complete.\n{review}')
                
        save_output(et, (width, height), mined_hash, brief, review, pixels)
    
    except KeyboardInterrupt:
        et = time.time() 
    
        p = np.mean(np.any(pixels != 0, axis=-1))
        print(f"Mining aborted at {p:.2%} progress\nTime elapsed: {et - st:,.2f}s\nMined image will not be saved to disk.")
    
        Image.fromarray(pixels, 'RGB').show()

if __name__ == '__main__':
    main()