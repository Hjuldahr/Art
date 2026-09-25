import math
import os
from PIL import Image

SOURCE_DIR = 'Source Images'
OUTPUT_DIR = 'Generated Images'

def polar_to_cartesian(radius: float, theta: float, x_offset: int, y_offset: int):
    # theta is in radians
    # polar is anchored at (0,0), so an offset is needed to denormalize it
    x = radius * math.cos(theta) + x_offset
    y = radius * math.sin(theta) + y_offset
    return x, y

def cartesian_to_polar(x: int, y: int, x_offset: int, y_offset: int):
    # polar is anchored at (0,0), so an offset is needed to normalize it
    offset_x, offset_y = x - x_offset, y - y_offset
    radius = math.hypot(offset_x, offset_y)
    theta = math.atan2(offset_y, offset_x)
    return radius, theta

def rgb_to_hue(rgb: tuple[int, int, int]):
    # hue is in degrees
    rgbn = [c / 255 for c in rgb]
    c_min, c_max = min(rgbn), max(rgbn)
    c_delta = c_max - c_min
    rn, gn, bn = rgbn
    
    if (c_delta == 0):
        return 0
    elif (c_max == rn):
        return 60 * (((gn - bn) / c_delta) % 6)
    elif (c_max == gn):
        return 60 * (((bn - rn) / c_delta) + 2)
    elif (c_max == bn):
        return 60 * (((rn - gn) / c_delta) + 4)
    else:
        return 0

def clamp(value, upper, lower=0):
    return min(max(lower, int(value)), upper)

def distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def bounds_check(x, y, width, height):
    return 0 <= x < width and 0 <= y < height

def hue_in_range(hue, start, end):
    if start <= end:
        return start <= hue <= end
    else:
        return hue >= start or hue <= end

def radial_sort(image, hue_start: float, hue_end: float):
    width, height = image.size
    #new_image = image.copy()
    new_image = Image.new('RGBA', image.size, (0,0,0,0))
    pixels = image.load()
    new_pixels = new_image.load()
    
    collecting = False
    all_points = []
    
    for y in range(height):
        for x in range(width):
            rgb = pixels[x, y]
            hue = rgb_to_hue(rgb)
            
            if hue_in_range(hue, hue_start, hue_end):
                all_points.append((x, y)) 
    
    # choose centroid using the positional per-axis average of all matching pixels
    center_x = sum(point[0] for point in all_points) // len(all_points)
    center_y = sum(point[1] for point in all_points) // len(all_points)
    
    # find distance between furthest corner and centroid
    max_radius = int(max(distance(center_x, center_y, 0, 0), 
                         distance(center_x, center_y, 0, height),
                         distance(center_x, center_y, width, 0),
                         distance(center_x, center_y, width, height)))
    
    collecting = False
    x, px, y, py = -1, -1, -1, -1
    values = []
    
    for radius in range(1, max_radius):
        if (radius % 10 == 0):
            print(f'{radius / max_radius:0.1%}')
        #minimum number of degress number to radially scan a square
        degree_increment = 360 / (radius * 16)
        degrees = 0
        while degrees < 360: #soften transition by allowing overshoot
            radians = math.radians(degrees)
            x, y = polar_to_cartesian(radius, radians, center_x, center_y)
            x, y = int(x), int(y)
            
            if (x == px and y == py) or not bounds_check(x, y, width, height):
                degrees += degree_increment
                continue
            
            rgb = pixels[x, y]
            hue = rgb_to_hue(rgb)
            
            if hue_in_range(hue, hue_start, hue_end):
                collecting = True
                
            elif hue < hue_start or hue > hue_end:
                if collecting:
                    points = [value[:2] for value in values]
                    colours = sorted((value[2:] for value in values), key=lambda c: c[1])
                    
                    for (x2, y2), (rgb, _) in zip(points, colours):
                        r, g, b = rgb
                        new_pixels[x2, y2] = (r, g, b, 255)
                
                collecting = False   
                values = []
                
            if collecting:
                values.append((x, y, rgb, hue))   
                
            px, py = x, y   
            degrees += degree_increment   

    for a in range(0, 255, 255 // 10):
        print(a)
        for (x, y) in all_points:
            if 1 < x < width-1 and 1 < y < height-1:
                min_a = min(new_pixels[x + xo, y + yo][3] for xo, yo in ((-1,0),(0,1),(1,0),(0,-1)))
                if min_a == a:
                    r, g, b, _ = new_pixels[x, y]
                    new_pixels[x, y] = (r, g, b, a + 1)
            
    new_image = Image.alpha_composite(image.convert("RGBA"), new_image)
        
    return new_image  

parent_dir = os.path.dirname(__file__)
source_dir = os.path.join(parent_dir, SOURCE_DIR)
output_dir = os.path.join(parent_dir, OUTPUT_DIR)
os.makedirs(output_dir, exist_ok=True)

file_name = 'lobster-nebula-ngc-6357-diffuse-nebula-science-technology-0dff78-1024.jpg'

image = Image.open(os.path.join(source_dir, file_name)).convert("RGB")
sorted_image = radial_sort(image, 190, 310)
sorted_image.save(os.path.join(output_dir, f'radial-pxl-sorted-{file_name}.png'))
print('done')
sorted_image.show()

#TODO add cross image (original & sorted) edge blending to soften transitions