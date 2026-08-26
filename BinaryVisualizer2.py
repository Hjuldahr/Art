import math
from PIL import Image
from hilbertcurve.hilbertcurve import HilbertCurve
import os

def readFile(file_name):
    blocks = []
    with open(file_name, mode='rb') as f:
        while True:
            block = f.read(1)
            if not block:
                break
            blocks.append(block[0])
    return blocks

def next_power_of_two(x):
    return 1 << (x - 1).bit_length()

if __name__ == '__main__':
    file_name = 'c:\\Program Files\\FireAlpaca\\FireAlpaca64\\FireAlpaca20\\FireAlpaca.exe'
    blocks = readFile(file_name)

    total_blocks = len(blocks)
    side = int(math.floor(math.sqrt(total_blocks)))
    side = next_power_of_two(side)

    needed = side * side
    if total_blocks < needed:
        blocks.extend([0] * (needed - total_blocks))
    elif total_blocks > needed:
        blocks = blocks[:needed]

    image = Image.new('RGB', (side, side), (0, 0, 0))
    pixels = image.load()

    p = int(math.log2(side))
    hilbert = HilbertCurve(p, 2)
    for i in range(needed):
        x, y = hilbert.point_from_distance(i)
        v = blocks[i]
        pixels[x, y] = (v, v, v)

    name = os.path.splitext(os.path.basename(file_name))[0]
    os.makedirs('Generated Images', exist_ok=True)
    out_path = f'Generated Images/Binary_Art_{name}_hilbert.png'
    image.save(out_path)
    print(f"Saved: {out_path}")
