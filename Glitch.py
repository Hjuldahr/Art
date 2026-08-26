import math
import os
import random as r
from PIL import Image

def snow(old_image, snow_density: float):
    snow_density = min(max(0.0, snow_density), 1.0)
    
    width, height = old_image.size
    new_image = old_image.copy()
    new_pixels = new_image.load()
    
    for y in range(height):
        if r.random() < snow_density:  # row affected
            for x in range(width):
                if r.random() < 0.1:    # only some pixels flip
                    v = r.randint(0, 255)
                    new_pixels[x, y] = (v, v, v)
                
    return new_image

def colour_shift(old_image, shift: int = 5, directions: tuple = (-1, 0, 1)):
    width, height = old_image.size
    old_pixels = old_image.load()
    new_image = Image.new('RGB', (width, height), 0)
    new_pixels = new_image.load()
    
    for y in range(height):
        for x in range(width):
            new_pixels[x, y] = tuple(old_pixels[(x + directions[i] * shift) % width, (y + directions[i] * shift) % height][i] for i in range(3))
    
    return new_image

def screen_tear(old_image, tear_count: int, max_tear_offset: int, min_tear_spacing: int, drift_strength: float = 0.2):
    width, height = old_image.size
    old_pixels = old_image.load()
    new_image = old_image.copy()
    new_pixels = new_image.load()
    
    # Clamp tear_count
    tear_count = min(tear_count, height // min_tear_spacing)
    
    # Main tear points
    y_points = sorted(r.sample([n for n in range(0, height, min_tear_spacing)], tear_count))
    y_points.append(height)
    
    for i in range(tear_count):
        start_y = y_points[i]
        end_y = y_points[i + 1]
        base_offset = r.randint(-max_tear_offset, max_tear_offset)
        
        for y in range(start_y, end_y):
            # Smooth per-row drift using sine-like randomness
            drift = int(base_offset * (1 + drift_strength * r.uniform(-1, 1)))
            for x in range(width):
                new_pixels[x, y] = old_pixels[(x + drift) % width, y]
    
    return new_image

def generate_pallete() -> tuple[tuple[int, int, int]]:
    return tuple(tuple(((n >> i) & 1) * 255 for i in (2,1,0)) for n in range(1,7))

def checkerboarding(old_image, other_images: list, block_count: int, block_size: int):
    glitch_colours = generate_pallete()
    
    width, height = old_image.size
    max_blocks = (width // block_size) * (height // block_size)
    block_count = min(block_count, max_blocks)
    
    new_image = old_image.copy()
    new_pixels = new_image.load()

    # Pick block positions
    points = r.sample([(x, y) for x in range(0, width - block_size, block_size) for y in range(0, height - block_size, block_size)], block_count)

    for point in points:
        # Weighted choice to mimic real artifact frequency
        glitch_type = r.choices(
            population=[0, 1, 2, 3, 4, 5],
            weights=[20, 20, 25, 15, 10, 10],  # solid/primary more common
            k=1
        )[0]

        if glitch_type == 2:
            colour = r.choice(glitch_colours)
        elif glitch_type == 5:
            other_image = r.choice(other_images)
            other_pixels = other_image.load()
            other_width, other_height = other_image.size
            other_x, other_y = r.randrange(other_width), r.randrange(other_height)

        x_start, y_start = point
        x_end, y_end = x_start + block_size, y_start + block_size

        for y in range(y_start, y_end):
            for x in range(x_start, x_end):
                if glitch_type == 0:      # Solid black
                    new_pixels[x, y] = (0, 0, 0)
                elif glitch_type == 1:    # Solid white
                    new_pixels[x, y] = (255, 255, 255)
                elif glitch_type == 2:    # Bright primary
                    new_pixels[x, y] = colour
                elif glitch_type == 3:    # Black/white static
                    v = r.choice((0, 255))
                    new_pixels[x, y] = (v, v, v)
                elif glitch_type == 4:    # Corrupted noise (channel-dominant)
                    ch = r.choice([0, 1, 2])
                    pixel = [0, 0, 0]
                    pixel[ch] = r.randint(0, 255)
                    new_pixels[x, y] = tuple(pixel)
                elif glitch_type == 5:    # Wrong texture tile
                    new_pixels[x, y] = other_pixels[(x + other_x) % other_width, (y + other_y) % other_height]

    return new_image
    
def colour_distance(colour_1: tuple[int, int, int], colour_2: tuple[int, int, int]) -> float:
    red_mean = (colour_1[0] + colour_2[0]) / 2
    delta_c = math.sqrt((2 + (red_mean / 256)) * ((colour_1[0] - colour_2[0]) ** 2) + 4 * ((colour_1[1] - colour_2[1]) ** 2) + (2 + ((255 - red_mean) / 256)) * ((colour_1[2] - colour_2[2]) ** 2))
    return delta_c
    
def posterize(old_image, palette_size: int):
    palette_size = min(max(1, palette_size), 255)
    
    width, height = old_image.size
    old_pixels = old_image.load()
    new_image = old_image.copy()
    new_pixels = new_image.load()
    
    palette_image = old_image.convert("P", palette=Image.ADAPTIVE, colors=palette_size)
    palette_colours = palette_image.getpalette()[:3 * palette_size]
    palette_colours = [tuple(palette_colours[i:i + 3]) for i in range(0, len(palette_colours), 3)]
    
    # get most common
    conversion_cache = {}
                
    # remap to closest colours
    for y in range(height):
        for x in range(width):
            pixel_colour = old_pixels[x, y]
            
            if pixel_colour not in conversion_cache:
                conversion_cache[pixel_colour] = min(((palette_colour, colour_distance(pixel_colour, palette_colour)) for palette_colour in palette_colours), key=lambda e: e[1])[0]
                            
            new_pixels[x, y] = conversion_cache[pixel_colour]

    return new_image
    
iterations = 8
image_name = '07l679a8co411.jpg'
source_dir = os.path.realpath('./Art/Source Images')

other = [Image.open(os.path.join(source_dir, file_name)).convert('RGB') for file_name in os.listdir(source_dir)]
image = Image.open(f'./Art/Source Images/{image_name}').convert('RGB')

print(f'Pre-Iteration')
print('posterizing')
image = posterize(image, 32)

for i in range(iterations):
    print(f'Iteration {i+1}/{iterations}')
    print('checkering')
    image = checkerboarding(image, other, 32, 32)
    print('snowing')
    image = snow(image, 0.08)
    print('tearing')
    image = screen_tear(image, 3, 16, 8)

print(f'Post-Iteration')
print('shifting')
image = colour_shift(image)
print('exporting')
image.save(f'./Art/Generated Images/Glitch Art/glitch-{image_name}')
image.show()