import math
from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageEnhance

WIDTH = 1920
HEIGHT = 1080
SIZE = (WIDTH, HEIGHT)

PADDING = 25
MIN_RADIUS = 500
MAX_RADIUS = 750

BG = (1, 1, 1)
LINE = (0, 0, 0)

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
BASE_OFFSET = math.sqrt(3) / 2

for i in range(5):
    next_points = set()
    
    for (x, y) in points:
        r = random_radius()
        y_offset = r * BASE_OFFSET

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
            outline=LINE, 
            width=1
        )

        next_points.update((x, y) for x, y in vertices if 0 <= x < WIDTH and 0 <= y < HEIGHT)
        
    points = next_points.copy()

pixels = img.load()

unvisited = set([(x, y) for x in range(WIDTH) for y in range(HEIGHT) if pixels[x, y] == BG])
DELTAS = ((1, 0), (0, -1), (-1, 0), (0, 1))

while unvisited:
    xy = next(iter(unvisited))
    x, y = xy

    colour = hash(xy) & 0xFF_FF_FF # PIL Accepts colours in this format

    pixels[x, y] = colour
    fill_points = {xy}
    unvisited.remove(xy)

    while fill_points:
        next_points = set()

        for px, py in fill_points:
            for dx, dy in DELTAS:
                fx = px + dx
                fy = py + dy

                if not (0 <= fx < WIDTH and 0 <= fy < HEIGHT):
                    continue

                fxy = (fx, fy)
                if fxy not in unvisited:
                    continue

                pixels[fx, fy] = colour
                next_points.add(fxy)

        fill_points = next_points
        unvisited.difference_update(next_points)

points = set()
for y in range(HEIGHT):
    for x in range(WIDTH):
        edges = 0
        neighbours = 0
        if x > 0:
            edges += 1
            if pixels[x-1, y] == LINE:
                neighbours += 1
        if x < WIDTH-1:
            edges += 1
            if pixels[x+1, y] == LINE:
                neighbours += 1
        if y > 0:
            edges += 1
            if pixels[x, y-1] == LINE:
                neighbours += 1
        if y < HEIGHT-1:
            edges += 1
            if pixels[x, y+1] == LINE:
                neighbours += 1
                
        if neighbours >= edges - 1:
            points.add((x, y))
            
for x, y in points:
    pixels[x, y] = LINE

enhancer = ImageEnhance.Brightness(img)
img = enhancer.enhance(1.1)

output = Path(__file__).parent / 'Generated Images' / 'hexagons-1.png'
img.save(output)

img.show()