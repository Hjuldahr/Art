import os
from PIL import Image

def process(pixels, width, height, offset=10):
    new_pixels = [[(pixels[x - offset, y][0], pixels[x + offset, y][1], pixels[x + offset, y][2]) if offset <= x < width - offset else (0, 0, 0) for x in range(width)] for y in range(height)]
    
    for y in range(height):
        for x in range(width):
            pixels[x, y] = new_pixels[y][x]
    return pixels

SOURCE_NAME = '79avborlpyh61-ezgif.jpg'
SOURCE_DIR = 'Source Images'
OUTPUT_DIR = 'Generated Images'
OFFSET = 5

output_name = SOURCE_NAME.split('.')
output_name.insert(1, '-anaglyph.')
output_name = ''.join(output_name)

parent_dir = os.path.dirname(__file__)
source_path = os.path.join(parent_dir, SOURCE_DIR, SOURCE_NAME)
output_path = os.path.join(parent_dir, OUTPUT_DIR, output_name)

image = Image.open(source_path).convert('RGB')
pixels = image.load()
width, height = image.size

pixels = process(pixels, width, height, OFFSET)
image = image.crop((OFFSET, 0, width - OFFSET, height))
image.save(output_path)
image.show()