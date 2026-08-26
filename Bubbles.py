import math
from pathlib import Path
import random
import colorsys
import uuid
from PIL import Image, ImageDraw

PADDING = 5
MIN_R = 4
COUNT = 250
INTERVAL = 10
WIDTH, HEIGHT = 500, 500

class Circle:
    def __init__(self, x: int, y: int, r: int, fill_colour=None, edge_colour=None):
        self.x, self.y, self.r, self.fill_colour, self.edge_colour = x, y, r, fill_colour, edge_colour
        
    def distance(self, x: int, y: int) -> float:
        return math.sqrt((self.x - x)**2 + (self.y - y)**2)
    
    @staticmethod
    def find_centroid(circles: list[Circle]) -> tuple[int, int]:
        x, y = 0, 0
        
        for c in circles:
            x += c.x
            y += c.y
            
        n = len(circles)
        return (x // n, y // n)

def random_pastel():
    h = random.uniform(0.0, 1.0)
    s = random.uniform(0.1, 0.4)
    v = random.uniform(0.7, 1.0)
    
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    #inv_s = int((1.0 - v) * 255)
    r2, g2, b2 = colorsys.hsv_to_rgb(h, s + 0.3, v - 0.2) 
    
    return [
        (int(r * 255), int(g * 255), int(b * 255)), 
        #(inv_g, inv_g, inv_g)
        (int(r2 * 255), int(g2 * 255), int(b2 * 255))
    ]

BG = (250, 248, 246)
image = Image.new('RGB', (WIDTH, HEIGHT), BG)
draw = ImageDraw.Draw(image)

# Invisible main container circle
x, y = WIDTH // 2, HEIGHT // 2
x_centroid, y_centroid = x, y
r = min((x - PADDING, y - PADDING, WIDTH - PADDING - x, HEIGHT - PADDING - y))

circles = [Circle(x, y, r)]

for _ in range(COUNT * 2):
    if len(circles) >= COUNT: break
    
    x = int(random.triangular(PADDING, WIDTH - PADDING, x_centroid))
    y = int(random.triangular(PADDING, HEIGHT - PADDING, y_centroid))
    
    # 1. Find all circles containing this point
    containers = [c for c in circles if c.distance(x, y) < c.r]
    if not containers: continue
        
    # The parent is the tightest (smallest) circle containing the point
    parent = min(containers, key=lambda c: c.r)
    
    # Inside boundary: cannot go past the parent's edge
    max_r = parent.r - parent.distance(x, y)
    
    # Outside boundary: cannot overlap any other circle
    possible = True
    for c in circles:
        if c == parent: continue
        dist = c.distance(x, y)
        if dist < c.r:
            # If we are inside another circle that is smaller than our parent,
            # then that circle should have been the parent. 
            if c.r < parent.r: 
                possible = False
                break
        else:
            # Outside constraint: gap between point and circle edge
            max_r = min(max_r, dist - c.r)
            
    if possible and max_r > MIN_R:
        new_c = Circle(x, y, max_r, *random_pastel())
        draw.ellipse([x-max_r, y-max_r, x+max_r, y+max_r], fill=new_c.fill_colour, outline=new_c.edge_colour)
        circles.append(new_c)
        print(f"Circles placed: {len(circles)}/{COUNT}", end="\r")
        
        if len(circles) % INTERVAL == 0:
            x_centroid, y_centroid = Circle.find_centroid(circles[1:])

path = Path(__file__).parent / 'Generated Images' / f'bubbles {uuid.uuid4()}.png'
image.save(path)