import math
from pathlib import Path
from PIL import Image
import numpy as np

def get_color(byte_value):
    # 1. Null/Control/Whitespace (The absolute basics)
    if byte_value == 0x00:
        return (0, 0, 0)
    if byte_value in [0x09, 0x0A, 0x0D, 0x7F, 0xFF]:
        return (byte_value, 0, 0)

    # 2. Specific Instruction Ranges
    if 0x50 <= byte_value <= 0x5F:  # Push/Pop range (Purple)
        return (byte_value, 0, byte_value)
    
    if 0x40 <= byte_value <= 0x4F:  # REX Prefix range (Blue)
        return (0, 0, byte_value)
    
    # Common Padding (Cyan)
    if byte_value in [0x90, 0xCC]:
        return (0, byte_value, byte_value)

    # 3. General Printable ASCII (Green)
    if 0x20 <= byte_value <= 0x7E:
        return (0, byte_value, 0)

    # 4. Binary/Extended Data (Greyscale)
    return (byte_value, byte_value, byte_value)

if __name__ == '__main__':
    WIDTH = 1024 # Or 256, 512, etc.
    INPUT_PATH = Path('').resolve()
    OUTPUT_PATH = Path(__file__).parent / 'Generated Images' / f'Binary_{INPUT_PATH.stem}.png'

    data = INPUT_PATH.read_bytes()
    
    height = math.ceil(len(data) / WIDTH)
    total_pixels = WIDTH * height
    
    padded_data = data.ljust(total_pixels, b'\x00')
    
    lookup_table = np.array([get_color(i) for i in range(256)], dtype=np.uint8)
    pixel_array = lookup_table[np.frombuffer(padded_data, dtype=np.uint8)]

    pixel_array = pixel_array.reshape((height, WIDTH, 3))
    image = Image.fromarray(pixel_array, 'RGB')
            
    image.save(OUTPUT_PATH)
    image.show()