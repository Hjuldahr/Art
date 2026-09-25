from enum import Enum
import math
import random
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path
from uuid import uuid4

class Direction(Enum):
    NORTH = 0
    NORTH_EAST = 1
    EAST = 2
    SOUTH_EAST = 3
    SOUTH = 4
    SOUTH_WEST = 5
    WEST = 6
    NORTH_WEST = 7

def randbool():
    return random.random() < 0.5

def clamp(n):
    return min(max(0, math.floor(n)), 255)

EXPORT_PATH = Path(__file__).parent / 'Generated Images' / f'Lines-{uuid4()}.png'
LINE_COUNT_PER_SIDE = 15
WIDTH = 1920
HEIGHT = 1080
THICKNESS = 5
OFFSET = THICKNESS * 2
SIZE = (WIDTH, HEIGHT)
BGROUND = (0,0,0)
COLOUR_MASKS = ((1,0,0), (1,1,0), (0,1,0), (0,1,1), (0,0,1), (1,0,1))
COLOUR_MASK_COUNT = len(COLOUR_MASKS)
DIRECTIONS = tuple(Direction)

image = Image.new('RGB', SIZE, BGROUND)
draw = ImageDraw.Draw(image)

x_coords = [x for x in range(OFFSET, WIDTH - OFFSET, OFFSET)]
y_coords = [y for y in range(OFFSET, HEIGHT - OFFSET, OFFSET)]
COORD_COUNT = min(len(x_coords), len(y_coords))

random.shuffle(x_coords)
random.shuffle(y_coords)

colour_mode = 0

for i in range(COORD_COUNT):
    value = 255 * (i / COORD_COUNT)
    colour = tuple(clamp(value * mask) for mask in COLOUR_MASKS[colour_mode])
    
    x = x_coords[i]
    y = y_coords[i]
    
    for direction in random.sample(DIRECTIONS, k=random.randrange(2, 5)):
        match direction:
            case Direction.NORTH:
                draw.line([(x, y), (x, 0)], colour, THICKNESS)

            case Direction.NORTH_EAST:
                # Offset stops at the top edge (y=0) or right edge (x=WIDTH)
                offset = min(WIDTH - x, y)
                draw.line([(x, y), (x + offset, y - offset)], colour, THICKNESS)

            case Direction.EAST:
                draw.line([(x, y), (WIDTH, y)], colour, THICKNESS)

            case Direction.SOUTH_EAST:
                # Offset stops at the bottom edge (y=HEIGHT) or right edge (x=WIDTH)
                offset = min(WIDTH - x, HEIGHT - y)
                draw.line([(x, y), (x + offset, y + offset)], colour, THICKNESS)

            case Direction.SOUTH:
                draw.line([(x, y), (x, HEIGHT)], colour, THICKNESS)

            case Direction.SOUTH_WEST:
                # Offset stops at the bottom edge (y=HEIGHT) or left edge (x=0)
                offset = min(x, HEIGHT - y)
                draw.line([(x, y), (x - offset, y + offset)], colour, THICKNESS)

            case Direction.WEST:
                draw.line([(x, y), (0, y)], colour, THICKNESS)

            case Direction.NORTH_WEST:
                # Offset stops at the top edge (y=0) or left edge (x=0)
                offset = min(x, y)
                draw.line([(x, y), (x - offset, y - offset)], colour, THICKNESS)
    
    colour_mode = (colour_mode + 1) % COLOUR_MASK_COUNT 
    
image = image.filter(ImageFilter.GaussianBlur(2.0))
    
image.show()
image.save(EXPORT_PATH)