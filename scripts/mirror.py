import math
import random
from PIL import Image

def display(pixels: dict[tuple[int,int], int]):
    coords = tuple(pixels.keys())
    x, y = coords[0]
    min_x = x
    max_x = x
    min_y = y
    max_y = y
    
    for coord in coords[1:]:
        x, y = coord
        min_x = min(x, min_x)
        max_x = max(x + 1, max_x)
        min_y = min(y, min_y)
        max_y = max(y + 1, max_y)
    
    pixels_arr = [[pixels[(x, y)] for x in range(min_x, max_x)] for y in range(min_y, max_y)]
    
    for row in pixels_arr:
        for cell in row:
            print(cell, end=' ')
        print()

def select(pixels, x1, y1, x2, y2):
    selection = {}
    
    for y in range(y1, y2):
        for x in range(x1, x2):
            coord = (x, y)
            selection[coord] = pixels.get(coord, 0)
    
    return selection

def offset(pixels: dict[tuple[int,int]], x_offset: int, y_offset: int) -> dict[tuple[int,int], int]:
    offset_pixels = {(coord[0] + x_offset, coord[1] + y_offset): v for coord, v in pixels.items()}
    return offset_pixels

def flip(pixels: dict[tuple[int,int], int], direction: int) -> dict[tuple[int,int], int]:
    #0 = x-axis
    #1 = y-axis
    #2 = both
    coords = tuple(pixels.keys())
    x, y = coords[0]
    min_x = x
    max_x = x
    min_y = y
    max_y = y
    
    for coord in coords[1:]:
        x, y = coord
        min_x = min(x, min_x)
        max_x = max(x + 1, max_x)
        min_y = min(y, min_y)
        max_y = max(y + 1, max_y)
    
    flipped_pixels = {}

    if direction == 1:
        x_diff = max_x - min_x - 1
        
        for coord, pixel in pixels.items():
            x, y = coord
            x -= min_x
            x = x_diff - x
            x += min_x
            flipped_pixels[(x, y)] = pixel
            
    elif direction == 0:
        y_diff = max_y - min_y - 1
        
        for coord, pixel in pixels.items():
            x, y = coord
            y -= min_y
            y = y_diff - y
            y += min_y
            flipped_pixels[(x, y)] = pixel
            
    elif direction == 2:
        x_diff = max_x - min_x - 1
        y_diff = max_y - min_y - 1
        
        for coord, pixel in pixels.items():
            x, y = coord

            x -= min_x
            y -= min_y
            
            x = x_diff - x
            y = y_diff - y
            
            x += min_x
            y += min_y
            
            flipped_pixels[(x, y)] = pixel
            
    return flipped_pixels

def transform(values: tuple[int], x: int, y: int):
    new_pixels = {}
    
    # Define relative positions for each value's block (4 pixels)
    blocks = [
        [(0, 0), (3, 0), (0, 3), (3, 3)],  # values[0]
        [(1, 0), (2, 0), (1, 3), (2, 3)],  # values[1]
        [(0, 1), (0, 2), (3, 1), (3, 2)],  # values[2]
        [(1, 1), (2, 1), (1, 2), (2, 2)]   # values[3]
    ]
    
    for i, positions in enumerate(blocks):
        v = values[i]
        for dx, dy in positions:
            new_pixels[(x + dx, y + dy)] = v
    
    return new_pixels

def random_generate(size: int = 500):
    pixels = {}
    
    for y in range(0, size, 4):
        for x in range(0, size, 4):
            source = tuple(random.getrandbits(1) for _ in range(4))
            pixels.update(transform(source, x, y))
    
    image = Image.new('1', (size, size), 0)
    image_pixels = image.load()
    
    for (x, y), value in pixels.items():
        image_pixels[x, y] = value
        
    return image

def generate(number: int):
    bits = [int(v) for v in bin(number)[2:]]
    
    # number of 4-bit groups (blocks) needed
    num_blocks = math.ceil(len(bits) / 4)
    
    # side length in blocks (smallest square to fit all blocks)
    blocks_side = math.ceil(math.sqrt(num_blocks))
    
    # pad bits to fit full blocks * 4 bits each
    total_bits = blocks_side * blocks_side * 4
    bits.extend([0] * (total_bits - len(bits)))
    
    pixels = {}
    i = 0
    
    side_pixels = blocks_side * 4  # actual image side length in pixels
    
    for y in range(0, side_pixels, 4):
        for x in range(0, side_pixels, 4):
            pixels.update(transform(bits[i:i+4], x, y))
            i += 4
    
    image = Image.new('1', (side_pixels, side_pixels), 0)
    image_pixels = image.load()
    
    for (x, y), value in pixels.items():
        image_pixels[x, y] = value
        
    return image
    
#image = random_generate()
image = generate(826334)
image.save(f"./Art/Generated Images/mirror.jpg")
image.show()