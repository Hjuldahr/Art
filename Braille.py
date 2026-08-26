from pathlib import Path
from PIL import Image

BRAILLE_MAPPING = (0, 2, 4, 1, 3, 5, 6, 7)
MATRIX_WIDTH = 2
MATRIX_HEIGHT = 4
BRAILLE_START = 0x2800

def remap_braille(value: int) -> int:
    result = 0
    for old_bit, new_bit in enumerate(BRAILLE_MAPPING):
        if value & (1 << old_bit):
            result |= 1 << new_bit

    return result
    
BRAILLE_CELLS = { remap_braille(n): chr(BRAILLE_START + n) for n in range(256) }

#######################################

FILE_NAME = 'classical-art-inspiration.png'
SCALE = 0.25 #0.1
X_STRIDE_OFFSET = 0 # compensates for tracking, measured in braille dot equivelant
Y_STRIDE_OFFSET = 1 # compensates for leading, measured in braille dot equivelant
INVERTED = True # if the text medium is white on black

#######################################

BASE_PATH = Path(__file__).parent
INPUT_PATH = BASE_PATH / 'Source Images' / FILE_NAME
OUTPUT_PATH = BASE_PATH / 'Generated Images' / f'Binary_{INPUT_PATH.stem}.png'

img = Image.open(INPUT_PATH)
width, height = img.size

new_img = img.resize((int(width * SCALE), int(height * SCALE))).convert('1')
width, height = new_img.size
pixels = new_img.load()

cells = []

for y1 in range(0, height, MATRIX_HEIGHT + Y_STRIDE_OFFSET):
    for x1 in range(0, width, MATRIX_WIDTH + X_STRIDE_OFFSET):
        value = 0

        for n in range(8):
            x2 = n % MATRIX_WIDTH
            y2 = n // MATRIX_WIDTH

            if x1 + x2 >= width or y1 + y2 >= height:
                continue

            if (pixels[x1 + x2, y1 + y2] == 0) != INVERTED:
                value |= 1 << n

        cells.append(BRAILLE_CELLS[value])

    cells.append('\n')

text = ''.join(cells)
print(text)