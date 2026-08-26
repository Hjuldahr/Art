import math
import os
import random
from PIL import Image

OUTER_CIRCLE_RADIUS = 100
CIRCLE_COUNT = 3
BREAK_CHANCE = 0.125

# Monitor proportions
INIT_WIDTH = 1920
INIT_HEIGHT = 1028

FULL_CIRCLE = 360

COLOURS = (
    (27, 28, 23), # BLACK
    (218, 205, 199), # WHITE
    (224, 53, 43), # RED
    (78, 88, 139), # BLUE 
    (215, 168, 64) # YELLOW
)
BG_COLOUR = COLOURS[0]  

DIRECTIONS = (
    1, -1
)

def rotate_around_origin(x, y, theta):
    nx = round(x * math.cos(theta) - y * math.sin(theta))
    ny = round(x * math.sin(theta) + y * math.cos(theta))
    
    return (nx, ny)

def fit(v, base):
    return base * round(v / base)

def generate_arc_points(r):
    arcs = [[] for _ in range(FULL_CIRCLE)]
    
    for y in range(-r, 0):
        for x in range(0, r):
            if math.sqrt((x + 0.5) ** 2 + (y + 0.5) ** 2) > r:
                break
            
            arcs[0].append((x, y))
                
    for theta_deg in range(1, FULL_CIRCLE):
        theta_rad = math.radians(theta_deg)
        for (x, y) in arcs[0]:
            arcs[theta_deg].append(rotate_around_origin(x, y, theta_rad))
                
    return arcs

def generate():
    bg = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOUR)
    pixels = bg.load()

    for y1 in range(OUTER_CIRCLE_RADIUS, HEIGHT - OUTER_CIRCLE_RADIUS, OUTER_CIRCLE_RADIUS):
        for x1 in range(OUTER_CIRCLE_RADIUS, WIDTH - OUTER_CIRCLE_RADIUS, OUTER_CIRCLE_RADIUS):

            colour = random.choice(COLOURS)
            if colour == BG_COLOUR:
                continue

            for y2 in range(y1, y1 + OUTER_CIRCLE_RADIUS):
                for x2 in range(x1, x1 + OUTER_CIRCLE_RADIUS):
                    if 0 <= x2 < WIDTH and 0 <= y2 < HEIGHT:
                        pixels[x2, y2] = colour
    
    frames = []
    styling = tuple(
        (
            x, 
            y, 
            tuple(random.choice(QUADRANT_OFFSETS) for _ in range(len(ARCS_LAYERS))),
            tuple(random.choice(DIRECTIONS) for _ in range(len(ARCS_LAYERS))),
            tuple((random.choice(COLOURS), random.choice(COLOURS)) for _ in range(len(ARCS_LAYERS)))
        ) for x in range(OUTER_CIRCLE_RADIUS, WIDTH, OUTER_CIRCLE_DIAMETER) for y in range(OUTER_CIRCLE_RADIUS, HEIGHT, OUTER_CIRCLE_DIAMETER)
    )
    
    for theta_deg in range(1, FULL_CIRCLE):
        frame = bg.copy()
        pixels = frame.load()
        
        for (x1, y1, all_quadrant_offsets, all_directions, all_colours) in styling:
            for (arc_points, quadrant_offset_pairs, direction, colour_pairs) in zip(ARCS_LAYERS, all_quadrant_offsets, all_directions, all_colours):
                for (quadrant_offsets, colour) in zip(quadrant_offset_pairs, colour_pairs):
                    for quadrant_offset in quadrant_offsets:
                        for (x_offset, y_offset) in arc_points[((theta_deg + quadrant_offset) * direction) % FULL_CIRCLE]:
                            x2 = x1 + x_offset 
                            y2 = y1 + y_offset
                            if 0 <= x2 < WIDTH and 0 <= y2 < HEIGHT:
                                pixels[x2, y2] = colour

        frames.append(frame)
    
    os.makedirs(r'.\Art\Generated Gifs', exist_ok=True)   
    frames[0].save(r'.\Art\Generated Gifs\Circles 3.gif', save_all=True, append_images=frames[1:], duration=60, loop=0)

ARCS_LAYERS = tuple(
    generate_arc_points(OUTER_CIRCLE_RADIUS // o) for o in range(1, CIRCLE_COUNT + 1)
)

HALF_CIRCLE = FULL_CIRCLE // 2
QUARTER_CIRCLE = FULL_CIRCLE // 4

QUADRANT_OFFSETS = [
    (qp, tuple(
        (q + HALF_CIRCLE) % FULL_CIRCLE for q in qp)
    ) for qp in ((q, (q + QUARTER_CIRCLE) % FULL_CIRCLE) for q in range(0, FULL_CIRCLE, QUARTER_CIRCLE))
]

QUADRANT_OFFSETS.extend(
    (qp, tuple(
        (q + QUARTER_CIRCLE) % FULL_CIRCLE for q in qp)
    ) for qp in ((q, (q + HALF_CIRCLE) % FULL_CIRCLE) for q in range(0, FULL_CIRCLE, HALF_CIRCLE))
)

OUTER_CIRCLE_DIAMETER = OUTER_CIRCLE_RADIUS * 2

WIDTH = fit(INIT_WIDTH, OUTER_CIRCLE_DIAMETER)
HEIGHT = fit(INIT_HEIGHT, OUTER_CIRCLE_DIAMETER)

if __name__ == '__main__':
    generate()
    print('done')

# animated version, combine base, clockwise, anticlockwise quadrants for rotating circles