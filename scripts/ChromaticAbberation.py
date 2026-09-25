import math
import os
from PIL import Image

def process(pixels, width, height, offsets):
    channels = []
    cx, cy = width // 2, height // 2  # Image center
    
    for c, offset in enumerate(offsets):
        channel = []
        for y in range(height):
            row = []
            for x in range(width):
                dx, dy = x - cx, y - cy
                distance = math.hypot(dx, dy)
                strength = min(distance / 50, offset)  # Scale effect with distance
                if strength < x < width - strength and strength < y < height - strength:
                    angle = math.atan2(dy, dx)
                    x_offset = int(strength * math.cos(angle))
                    y_offset = int(strength * math.sin(angle))
                    row.append(pixels[x + x_offset, y + y_offset][c])
                else:
                    row.append(0)
            channel.append(row)
        channels.append(channel)
    
    for y in range(height):
        for x in range(width):
            rgb = (channels[0][y][x], channels[1][y][x], channels[2][y][x])
            pixels[x, y] = rgb
    return pixels

SOURCE_NAME = 'tree.jpg'
SOURCE_DIR = 'Source Images'
OUTPUT_DIR = 'Generated Images'
STRENGTH = 10

output_name = SOURCE_NAME.split('.')
output_name.insert(1, '-abberation.')
output_name = ''.join(output_name)

parent_dir = os.path.dirname(__file__)
source_path = os.path.join(parent_dir, SOURCE_DIR, SOURCE_NAME)
output_path = os.path.join(parent_dir, OUTPUT_DIR, output_name)

offsets = tuple(offset * STRENGTH for offset in (3, 1, 2))
max_offsets = max(offsets)

image = Image.open(source_path).convert('RGB')
pixels = image.load()
width, height = image.size


pixels = process(pixels, width, height, offsets)
image = image.crop((max_offsets, max_offsets, width - max_offsets, height - max_offsets))
image.save(output_path)
image.show()