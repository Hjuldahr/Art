from pathlib import Path
import random
from PIL import Image

RED = (224, 53, 43)
ORED = (179, 171, 151)
BLUE = (78, 88, 139)
YELLOW = (215, 168, 64)
GREY = (150, 154, 165)
WHITE = (218, 205, 199)
BLACK = (27, 28, 23)
FLOOD_FILL_OFFSETS = ((0,-1),(1,0),(0,1),(-1,0))
LINE = tuple(v-1 for v in BLACK) #placeholder
COLOURS = (RED,ORED,BLUE,YELLOW,GREY,BLACK)
NOISE = (-1, 1)

def axis_check(v, min_v, max_v) -> int:
    return min_v <= v < max_v

def bound_check(x, y, min_x, min_y, max_x, max_y) -> int:
    return axis_check(x, min_x, max_x) and axis_check(y, min_y, max_y)

def generate_lines(size: tuple[int,int], point_count: int, line_width: int, colour_count: int):
    half_line_width = line_width // 2
    image = Image.new('RGB', size, WHITE)
    width, height = size
    pixels = image.load()
    
    #draw lines
    for x1, y1 in ((random.randrange(width), random.randrange(height)) for _ in range(point_count)):
        mode = True
        
        if random.getrandbits(1): #vertical
            for y2 in range(height):
                if pixels[x1, y2] == LINE:
                    mode = random.getrandbits(1)
                    
                if mode:
                    pixels[x1, y2] = LINE
        
        else: #horizontal
            for x2 in range(width):
                if pixels[x2, y1] == LINE:
                    mode = random.getrandbits(1)
                    
                if mode:
                    pixels[x2, y1] = LINE
    
    #bolden lines
    for y1 in range(half_line_width, height - half_line_width):
        for x1 in range(half_line_width, width - half_line_width):
            if pixels[x1, y1] == LINE:
                for y2 in range(y1 - half_line_width, y1 + half_line_width + 1):
                    for x2 in range(x1 - half_line_width, x1 + half_line_width + 1):
                        if pixels[x2, y2] != LINE:
                            pixels[x2, y2] = BLACK
    
    #floodfill cells
    i = 0
    while i < colour_count:
        x1, y1 = random.randrange(width), random.randrange(height)
        
        if pixels[x1, y1] == WHITE:
            colour = random.choice(COLOURS)
            current_points = [(x1, y1)]
            pixels[x1, y1] = colour
            
            while True:
                next_points = []
                for x2, y2 in current_points:
                    for new_point in ((x2 + x0, y2 + y0) for x0, y0 in FLOOD_FILL_OFFSETS):
                        x3, y3 = new_point
                        if bound_check(x3, y3, 0, 0, width, height) and pixels[x3, y3] == WHITE:
                            next_points.append(new_point)
                            pixels[x3, y3] = colour
                        
                if not next_points:
                    break
                current_points = next_points[:]
            
            i += 1
            
    #noise
    for y in range(0, height):
        for x in range(0, width):
            pixels[x, y] = tuple(min(max(0, v + random.randint(NOISE[0], NOISE[1])), 255) for v in pixels[x, y])

    return image

batch_size = 15

img_size = 200
img_ratios = ((2,3),(2,2),(3,2))
upscale_factor = 4

min_lines = 8
max_lines = 12
line_width = 3

min_coloured_cells = 6
max_coloured_cells = 8

root = Path(__file__).parent / "Generated Images" / "piet"
root.mkdir(exist_ok=True)

for i in range(1, batch_size + 1):
    print(i)
    
    rx, ry = random.choice(img_ratios)
    size = (img_size * rx, img_size * ry)
    lines = random.randrange(min_lines, max_lines)
    coloured_cells = random.randrange(min_coloured_cells, max_coloured_cells)
    
    image = generate_lines(size, lines, line_width, coloured_cells)
    image = image.resize((img_size * rx * upscale_factor, img_size * ry * upscale_factor), Image.NEAREST)
    
    image.save(root / f"piet_{i}.jpg", 'jpeg')