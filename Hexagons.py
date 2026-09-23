import math
import random

from PIL import Image, ImageDraw

WIDTH = 1920
HEIGHT = 1080
SIZE = (WIDTH, HEIGHT)

PADDING = 15
MIN_RADIUS = 100
MAX_RADIUS = 500

BG = (255, 255, 255)

def random_point() -> tuple[int, int]:
    return (
        random.randrange(PADDING, WIDTH - PADDING), 
        random.randrange(PADDING, HEIGHT - PADDING)
    )
    
def random_radius() -> float:
    return random.randint(MIN_RADIUS, MAX_RADIUS)

img = Image.new('RGB', SIZE, BG)
draw = ImageDraw.ImageDraw(img)

points = { random_point() }
next_points = set()

for i in range(5):
    for (x, y) in points:
        r = random_radius()
        y_offset = r * math.sqrt(3) / 2

        vertices = [
            (x + r, y),
            (x + r / 2, y + y_offset),
            (x - r / 2, y + y_offset),
            (x - r, y),
            (x - r / 2, y - y_offset),
            (x + r / 2, y - y_offset)
        ]
        
        draw.polygon(
            vertices,
            outline=(0, 0, 0), 
            width=1
        )

        next_points.update([(x % WIDTH, y % HEIGHT) for x, y in vertices if random.random() < 0.5])
        
    points = next_points.copy()
    next_points = set()

img.show()