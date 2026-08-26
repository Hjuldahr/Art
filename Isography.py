import math
import random
from PIL import Image, ImageDraw

# Canvas setup
WIDTH, HEIGHT = 500, 500
HALF_WIDTH = WIDTH // 2
HALF_HEIGHT = HEIGHT // 2

# Cube dimensions
THEODORUS = math.sqrt(3)
Px, Py = 50, 50  # cube width/height

# Hexagon points
HEX_PTS = (
    (-THEODORUS * (Px / 4), Py / 4),
    (-THEODORUS * (Px / 4), -Py / 4),
    (0, -Py / 2),
    (THEODORUS * (Px / 4), -Py / 4),
    (THEODORUS * (Px / 4), Py / 4),
    (0, Py / 2)
)
HEX_CTR = (0, 0)

# Quads for faces
BL_QUAD = (HEX_PTS[0], HEX_PTS[1], HEX_CTR, HEX_PTS[5])
BR_QUAD = (HEX_PTS[5], HEX_CTR, HEX_PTS[3], HEX_PTS[4])
T_QUAD  = (HEX_CTR, HEX_PTS[1], HEX_PTS[2], HEX_PTS[3])

# Shading
T_SHADING = 1.0
BL_SHADING = 0.7
BR_SHADING = 0.5

# Outline
OUTLINE_COLOUR = (0,0,0)
OUTLINE_THICKNESS = 1

def draw_cube(x, y, z, colour, draw: ImageDraw.ImageDraw):
    """Draw a single isometric cube at 3D coordinates (x, y, z)."""
    iso_x = (x - z) / math.sqrt(2) + HALF_WIDTH
    iso_y = (x + 2 * y + z) / math.sqrt(6) + HALF_HEIGHT

    draw.polygon([(qx + iso_x, qy + iso_y) for qx, qy in T_QUAD],
                 tuple(int(c * T_SHADING) for c in colour),
                 OUTLINE_COLOUR, OUTLINE_THICKNESS)
    draw.polygon([(qx + iso_x, qy + iso_y) for qx, qy in BL_QUAD],
                 tuple(int(c * BL_SHADING) for c in colour),
                 OUTLINE_COLOUR, OUTLINE_THICKNESS)
    draw.polygon([(qx + iso_x, qy + iso_y) for qx, qy in BR_QUAD],
                 tuple(int(c * BR_SHADING) for c in colour),
                 OUTLINE_COLOUR, OUTLINE_THICKNESS)

def draw_line(x1, y1, z1, x2, y2, z2, colour, width, draw: ImageDraw.ImageDraw):
    """Draw a single isometric cube at 3D coordinates (x, y, z)."""
    iso_x_1 = (x1 - z1) / math.sqrt(2) + HALF_WIDTH
    iso_y_1 = (x1 + 2 * y1 + z1) / math.sqrt(6) + HALF_HEIGHT
    
    iso_x_2 = (x2 - z2) / math.sqrt(2) + HALF_WIDTH
    iso_y_2 = (x2 + 2 * y2 + z2) / math.sqrt(6) + HALF_HEIGHT

    draw.line(((iso_x_1, iso_y_1), (iso_x_2, iso_y_2)), colour, width)

# Exact grid spacing
"""
step_x = Px * 0.6
step_y = Py * 0.6
step_z = Px * 0.6

# Create image
image = Image.new('RGB', (WIDTH, HEIGHT), (24, 24, 24))
draw = ImageDraw.Draw(image)

# Draw cubes in a true 3D isometric grid
for n in range(128):
    x = random.randint(-6, 6) * step_x
    y = random.randint(-6, 6) * step_y
    z = random.randint(-6, 6) * step_z
    draw_cube(x, y, z, (255, 255, 255), draw)
"""
image = Image.new('RGB', (WIDTH, HEIGHT), (255, 0, 0))
draw = ImageDraw.Draw(image)

step_size = 75
size = 150

for z in range(-size, size, step_size):
    for y in range(size, -size, -step_size):
        for x in range(-size, size, step_size):
            draw_cube(x, y, z, (255, 255, 255), draw)

for i in range(0, 200, 75):
    for j in range(0, 300, 75):
        """
        draw_line(
            0, 30 + i, -j, 
            0, 60 + i, -j, 
            (0, 0, 0),
            2, draw
        )
    
        draw_line(
            -j, 30 + i, 0, 
            -j, 60 + i, 0, 
            (0, 0, 0),
            2, draw
        )
        
        draw_line(
            -30 - i, 0, -j, 
            -60 - i, 0, -j, 
            (0, 0, 0),
            2, draw
        )
        
        draw_line(
            -j, 0, -30 - i, 
            -j, 0, -60 - i, 
            (0, 0, 0),
            2, draw
        )

        draw_line(
            0, j, -30 - i, 
            0, j, -60 - i, 
            (0, 0, 0),
            2, draw
        )
        
        draw_line(
            -30 - i, j, 0, 
            -60 - i, j, 0, 
            (0, 0, 0),
            2, draw
        )

        draw_line(
            0, -j, 30 + i, 
            0, -j, 45 + i, 
            (0, 0, 0),
            2, draw
        )
        """
        draw_line(
            30 + i, -j, 0, 
            45 + i, -j, 0, 
            (0, 0, 0),
            2, draw
        )
        
        draw_line(
            -j, 30 + i, -225, 
            -j, 45 + i, -225, 
            (0, 0, 0),
            2, draw
        )

        draw_line(
            -225, 30 + i, -j, 
            -225, 45 + i, -j, 
            (0, 0, 0),
            2, draw
        )
        
        draw_line(
            0, -j, 30 + i, 
            0, -j, 45 + i, 
            (0, 0, 0),
            2, draw
        )

        draw_line(
            -j, 225, 30 - i - 75, 
            -j, 225, 45 - i - 75, 
            (0, 0, 0),
            2, draw
        )
        
image.show()