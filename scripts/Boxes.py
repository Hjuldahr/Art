from __future__ import annotations
import math
from pathlib import Path
import random
import colorsys
import uuid
from PIL import Image, ImageDraw

PADDING = 15
MIN_SIDE = 4
RADIUS = 2.5
COUNT = 250
INTERVAL = 10
WIDTH, HEIGHT = 500, 500

class Box:
    def __init__(self, x: int, y: int, w: int, h: int, fill_colour=None, edge_colour=None):
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.fill_colour, self.edge_colour = fill_colour, edge_colour
        
    def distance(self, x: int, y: int) -> float:
        return math.sqrt((self.x - x)**2 + (self.y - y)**2)
    
    @property
    def x_w(self) -> int:
        return self.x + self.w
    
    @property
    def y_h(self) -> int:
        return self.y + self.h
    
    @property
    def p_0(self) -> tuple[int, int]:
        return (self.x, self.y)
        
    @property
    def p_1(self) -> tuple[int, int]:
        return (self.x_w, self.y)    
        
    @property
    def p_2(self) -> tuple[int, int]:
        return (self.x_w, self.y_h)     
        
    @property
    def p_3(self) -> tuple[int, int]:
        return (self.x, self.y_h)      
        
    @property
    def points(self) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]:
        return (self.p_0, self.p_1, self.p_2, self.p_3)
    
    def intersects(self, other: Box) -> bool:
        return not (
            self.x_w <= other.x or
            self.x >= other.x_w or
            self.y_h <= other.y or
            self.y >= other.y_h
        )
    
    def contains(self, other: Box) -> bool:
        return (
            self.x <= other.x and
            self.y <= other.y and
            self.x_w >= other.x_w and
            self.y_h >= other.y_h
        )
        
    def is_invalid(self, other: Box) -> bool:
        return (
            self.intersects(other)
            and not self.contains(other)
            and not other.contains(self)
        )    
    
    @staticmethod
    def find_centroid(boxes: list[Box]) -> tuple[float, float]:
        x, y = 0, 0
        
        for b in boxes:
            x += b.x + b.w / 2
            y += b.y + b.h / 2
            
        n = len(boxes)
        return (x / n, y / n)

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

boxes = []

for _ in range(10_000):
    if len(boxes) >= COUNT: break
    
    x = random.randrange(PADDING, WIDTH - PADDING - MIN_SIDE)
    y = random.randrange(PADDING, HEIGHT - PADDING - MIN_SIDE)
    
    w = random.randrange(MIN_SIDE, WIDTH - x - PADDING)
    h = random.randrange(MIN_SIDE, HEIGHT - y - PADDING)
    
    new_box = Box(x, y, w, h, *random_pastel())
    
    if any(b.is_invalid(new_box) for b in boxes):
        continue
    
    draw.rounded_rectangle([new_box.p_0, new_box.p_2], RADIUS, outline=new_box.edge_colour)
    boxes.append(new_box)
    
    print(f"Boxes placed: {len(boxes)}/{COUNT}", end="\r")

path = Path(__file__).parent / 'Generated Images' / f'boxes {uuid.uuid4()}.png'
image.save(path)