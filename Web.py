import os
from PIL import Image
import math
import random

def interval(num):
    return int('1' + '0' * max(len(str(num)) - 2, 1))

def calculatePaths(width, height):
    edge_points = [(x0, y0) for x1, x2, y1, y2 in (
        (0, width, 0, 1),
        (0, width, height - 1, height),
        (0, 1, 1, height - 1),
        (width - 1, width, 1, height - 1)
    ) for x0 in range(x1, x2) for y0 in range(y1, y2)]
    
    random.shuffle(edge_points)
    path = []
    l = len(edge_points)
    inter = interval(l)

    for i in range(0, l - 1):
        x1, y1 = edge_points[i]
        x2, y2 = edge_points[i + 1]
        
        dx = x2 - x1
        dy = y2 - y1
        mag = math.hypot(dx, dy)
        if mag == 0:
            continue
        
        dx /= mag
        dy /= mag
        
        x, y = x1, y1
        while 0 <= x < width and 0 <= y < height:
            coords = (int(x), int(y))
            if not path or path[-1] != coords:
                path.append(coords)
            x += dx
            y += dy
        
        if i % inter == 0:
            print(f'{i}/{l}')
    
    print(f'{len(edge_points)}/{l}')
    return path

def draw(points, width, height):
    image = Image.new('RGB', (width, height), (0, 0, 0))
    pixels = image.load()
    
    l = len(points)
    inter = interval(l)
    
    for i, point in enumerate(points, start=1):
        x, y = point
        v = int(255 * (i / l))
        pixels[x, y] = (v, v, v)
        
        if i % inter == 0:
            print(f'{i}/{l}')
        
    return image

if __name__ == '__main__':
    OUTPUT_DIR = 'Generated Images'

    parent_dir = os.path.dirname(__file__)
    output_dir = os.path.join(parent_dir, OUTPUT_DIR)
    os.makedirs(output_dir, exist_ok=True)
    
    width, height = 3000, 2000
    
    print("weaving web")
    points = calculatePaths(width, height)
    
    print("drawing image")
    image = draw(points, width, height)
    
    print("saving image")
    output_path = os.path.join(output_dir, 'Web3.jpg')
    image.save(output_path)
    image.show()