from __future__ import annotations
from collections import defaultdict
import math
from pathlib import Path
import random
from PIL import Image, ImageDraw

class Circle:
    def __init__(self, xy: tuple[int, int], r: float, c: tuple[int, int, int]):
        self.xy = xy
        self.r = r
        self.c = c
        
    def __repr__(self):
        return f'Circle(xy={self.xy}, r={self.r}, c={self.c})'
    
    def __str__(self):
        return f'({self.xy}, {self.r}, {self.c})'

DELTAS = tuple((rd, xd, yd) for rd in range(-1, 2) for yd in range(-3, 4) for xd in range(-3, 4))

def compare(width: int, height: int, pixels_a: Image.PixelAccess, pixels_b: Image.PixelAccess):
    difference = 0

    for y in range(height):
        for x in range(width):
            r1, g1, b1 = pixels_a[x, y]
            r2, g2, b2 = pixels_b[x, y]
            difference += ((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2)

    return difference

def calculate_brightness(colour: tuple[int, int, int]):
    return 0.299 * colour[0] + 0.587 * colour[1] + 0.114 * colour[2]

def draw_circles(circles: list[Circle], base_image: Image.Image):
    new_image = base_image.copy()
    draw = ImageDraw.ImageDraw(new_image)
    for circle in circles:
        draw.circle(circle.xy, circle.r, outline=circle.c)
    return new_image

def mutate_circle(width: int, height: int, min_radius: float, max_radius: float, circle: Circle):
    x, y = circle.xy
    rd, xd, yd = random.choice(DELTAS)
    
    xy = ((x + xd) % width, (y + yd) % height)
    r = min(max(min_radius, circle.r + rd), max_radius)
    
    return Circle(xy, r, circle.c)

def mutate(width: int, height: int, min_radius: float, max_radius: float, circles: list[Circle]):
    new_circles = (mutate_circle(width, height, min_radius, max_radius, circle) for circle in circles)
    new_circles = sorted(new_circles, key=lambda c: c.r, reverse=True)
    return new_circles

def distance(x1: int, y1: int, x2: int, y2: int):
    return (x1 - x2) ** 2 + (y1 - y2) ** 2
        
if __name__ == '__main__': 
    ################# 
    MAX_ITERATIONS = 1000
    TEMPERATURE = 10
    FILENAME = 'classical-art-inspiration.png'
    ################# 

    base_path = Path(__file__).parent
    in_path = base_path / 'Source Images' / FILENAME
    out_path = base_path / 'Generated Images' / f'ringularity_{FILENAME}'
    
    source_image = Image.open(in_path).convert("RGB") # .quantize(colors=255)
    source_pixels = source_image.load()
    
    #source_image.getcolors(RING_COUNT)
    
    width, height = source_image.size
    max_radius = min(source_image.size) // 2
    min_radius = 5

    colours = defaultdict(list)
    x_centroids = defaultdict(int)
    y_centroids = defaultdict(int)
    
    for y in range(height):
        for x in range(width):
            colour = source_pixels[x, y]
            colours[colour].append((x, y))
            
            x_centroids[colour] += x
            y_centroids[colour] += y

    circles = []
    n_t = 0
    base_colour = None
    
    for colour, points in colours.items():
        n = len(points)
        xc = x_centroids[colour] / n
        yc = y_centroids[colour] / n
        
        radius = random.randint(min_radius, max_radius)
        # seems to impede convergance times more than true randomness
        #distances = [distance(xc, x, yc, y) for x, y in points]
        #radius = math.sqrt(random.choice(distances))
        
        circles.append(Circle((xc, yc), radius, colour))
        
        if n > n_t:
            n_t = n
            base_colour = colour
        
    circles = sorted(circles, key=lambda c: c.r, reverse=True)
    
    base_image = Image.new('RGB', source_image.size, base_colour)
    new_image = draw_circles(circles, base_image)
    new_pixels = new_image.load()

    difference = compare(width, height, source_pixels, new_pixels)
    print(-1, difference)

    # uses simulated annealing to construct the image from rings
    for i in range(MAX_ITERATIONS):
        temp_circles = mutate(width, height, min_radius, max_radius, circles)
        
        new_image = draw_circles(temp_circles, base_image)
        new_pixels = new_image.load()
        new_difference = compare(width, height, source_pixels, new_pixels)
        
        delta = new_difference - difference
        if delta <= 0:
            accepted = True
        else:
            probability = math.exp(-delta / TEMPERATURE)
            accepted = random.random() < probability
        
        if accepted:
            print(i, new_difference, delta)
            circles = temp_circles
            difference = new_difference
            
    new_image.save(out_path)
    new_image.show()