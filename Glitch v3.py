import math
import os
import random as r
from PIL import Image, ImageFilter

# -----------------------------
# Utility functions
# -----------------------------
def colour_distance(c1, c2):
    red_mean = (c1[0] + c2[0]) / 2
    return math.sqrt(
        (2 + red_mean / 256) * ((c1[0] - c2[0]) ** 2) +
        4 * ((c1[1] - c2[1]) ** 2) +
        (2 + (255 - red_mean) / 256) * ((c1[2] - c2[2]) ** 2)
    )

def posterize(old_image, palette_size):
    palette_size = min(max(1, palette_size), 255)
    width, height = old_image.size
    old_pixels = old_image.load()
    new_image = old_image.copy()
    new_pixels = new_image.load()

    palette_image = old_image.convert("P", palette=Image.ADAPTIVE, colors=palette_size)
    palette_colours = palette_image.getpalette()[:3*palette_size]
    palette_colours = [tuple(palette_colours[i:i+3]) for i in range(0, len(palette_colours), 3)]

    cache = {}
    for y in range(height):
        for x in range(width):
            pixel = old_pixels[x, y]
            if pixel not in cache:
                closest = min(((c, colour_distance(pixel, c)) for c in palette_colours), key=lambda e: e[1])[0]
                cache[pixel] = closest
            new_pixels[x, y] = cache[pixel]

    return new_image

def generate_palette():
    return tuple(tuple(((n >> i) & 1) * 255 for i in (2,1,0)) for n in range(1,7))

# -----------------------------
# Snow effects
# -----------------------------
def snow_full(old_image, density):
    density = max(0.0, min(1.0, density))
    width, height = old_image.size
    new_image = old_image.copy()
    pixels = new_image.load()

    for _ in range(int(width*height*density)):
        x, y = r.randrange(width), r.randrange(height)
        v = r.randint(0,255)
        pixels[x,y] = (v,v,v)

    return new_image

def snow_stripes(old_image, density):
    density = max(0.0, min(1.0, density))
    width, height = old_image.size
    new_image = old_image.copy()
    pixels = new_image.load()

    for y in range(height):
        if r.random() < density:
            for x in range(width):
                if r.random() < 0.1:
                    v = r.randint(0,255)
                    pixels[x,y] = (v,v,v)

    return new_image

# -----------------------------
# Color shifting (RGB split)
# -----------------------------
def colour_shift(old_image, max_shift=5):
    width, height = old_image.size
    old_pixels = old_image.load()
    new_image = Image.new('RGB', (width, height), 0)
    new_pixels = new_image.load()

    directions = [r.choice([-1,0,1]) for _ in range(3)]  # per-channel drift
    for y in range(height):
        for x in range(width):
            new_pixels[x,y] = tuple(
                old_pixels[(x + directions[i]*r.randint(0, max_shift)) % width,
                           (y + directions[i]*r.randint(0, max_shift)) % height][i]
                for i in range(3)
            )
    return new_image

# -----------------------------
# Screen tears
# -----------------------------
def screen_tear_horizontal(old_image, tear_count, max_offset, min_spacing, drift_strength=0.2):
    width, height = old_image.size
    pixels_old = old_image.load()
    new_image = old_image.copy()
    pixels_new = new_image.load()

    tear_count = min(tear_count, height // min_spacing)
    y_points = sorted(r.sample([n for n in range(0, height, min_spacing)], tear_count))
    y_points.append(height)

    for i in range(tear_count):
        start, end = y_points[i], y_points[i+1]
        base_offset = r.randint(-max_offset, max_offset)
        for y in range(start, end):
            drift = int(base_offset * (1 + drift_strength*r.uniform(-1,1)))
            for x in range(width):
                pixels_new[x,y] = pixels_old[(x+drift)%width, y]

    return new_image

def screen_tear_vertical(old_image, tear_count, max_offset, min_spacing, drift_strength=0.2):
    width, height = old_image.size
    pixels_old = old_image.load()
    new_image = old_image.copy()
    pixels_new = new_image.load()

    tear_count = min(tear_count, width // min_spacing)
    x_points = sorted(r.sample([n for n in range(0, width, min_spacing)], tear_count))
    x_points.append(width)

    for i in range(tear_count):
        start, end = x_points[i], x_points[i+1]
        base_offset = r.randint(-max_offset, max_offset)
        for x in range(start, end):
            drift = int(base_offset * (1 + drift_strength*r.uniform(-1,1)))
            for y in range(height):
                pixels_new[x,y] = pixels_old[x, (y+drift)%height]

    return new_image

# -----------------------------
# Checkerboarding
# -----------------------------
def checkerboarding_blocks(old_image, other_images, block_count, block_size):
    glitch_colours = generate_palette()
    width, height = old_image.size
    max_blocks = (width // block_size)*(height // block_size)
    block_count = min(block_count, max_blocks)

    new_image = old_image.copy()
    pixels = new_image.load()

    points = r.sample([(x,y) for x in range(0,width-block_size,block_size)
                              for y in range(0,height-block_size,block_size)], block_count)

    for x0, y0 in points:
        glitch_type = r.choices([0,1,2,3,4,5], weights=[20,20,25,15,10,10], k=1)[0]

        if glitch_type == 2:
            colour = r.choice(glitch_colours)
        elif glitch_type == 5 and other_images:
            other_image = r.choice(other_images)
            other_pixels = other_image.load()
            other_w, other_h = other_image.size
            other_x, other_y = r.randrange(other_w), r.randrange(other_h)

        for y in range(y0, min(y0+block_size,height)):
            for x in range(x0, min(x0+block_size,width)):
                if glitch_type == 0:
                    pixels[x,y] = (0,0,0)
                elif glitch_type == 1:
                    pixels[x,y] = (255,255,255)
                elif glitch_type == 2:
                    pixels[x,y] = colour
                elif glitch_type == 3:
                    v = r.choice([0,255])
                    pixels[x,y] = (v,v,v)
                elif glitch_type == 4:
                    ch = r.choice([0,1,2])
                    pix = [0,0,0]
                    pix[ch] = r.randint(0,255)
                    pixels[x,y] = tuple(pix)
                elif glitch_type == 5 and other_images:
                    pixels[x,y] = other_pixels[(x+other_x)%other_w, (y+other_y)%other_h]

    return new_image

def checkerboarding_stripes(old_image, other_images, block_count, block_size, band_chance=0.3):
    glitch_colours = generate_palette()
    width, height = old_image.size
    max_blocks = (width // block_size)*(height // block_size)
    block_count = min(block_count, max_blocks)

    new_image = old_image.copy()
    pixels = new_image.load()

    points = [(x,y) for x in range(0,width-block_size,block_size)
                       for y in range(0,height-block_size,block_size)]
    chosen = r.sample(points, block_count)

    for x0,y0 in chosen:
        glitch_type = r.choices([0,1,2,3,4,5], weights=[20,20,25,15,10,10], k=1)[0]

        if r.random() < band_chance:
            if r.choice([True, False]):
                x1, y1 = width, y0 + block_size
            else:
                x1, y1 = x0 + block_size, height
        else:
            x1, y1 = x0 + block_size, y0 + block_size

        if glitch_type == 2:
            colour = r.choice(glitch_colours)
        elif glitch_type == 5 and other_images:
            other_image = r.choice(other_images)
            other_pixels = other_image.load()
            other_w, other_h = other_image.size
            other_x, other_y = r.randrange(other_w), r.randrange(other_h)

        for y in range(y0, min(y1,height)):
            for x in range(x0, min(x1,width)):
                if glitch_type == 0:
                    pixels[x,y] = (0,0,0)
                elif glitch_type == 1:
                    pixels[x,y] = (255,255,255)
                elif glitch_type == 2:
                    pixels[x,y] = colour
                elif glitch_type == 3:
                    v = r.choice([0,255])
                    pixels[x,y] = (v,v,v)
                elif glitch_type == 4:
                    pixels[x,y] = tuple(r.randint(0,255) for _ in range(3))
                elif glitch_type == 5 and other_images:
                    pixels[x,y] = other_pixels[(x+other_x)%other_w,(y+other_y)%other_h]

    return new_image

# -----------------------------
# Main pipeline
# -----------------------------
def glitch_pipeline(source_image_path, source_dir, iterations=16, output_dir='./Art/Generated Images/Glitch Art', palette_size=32):
    # Load source image
    image_name = os.path.basename(source_image_path)
    image = Image.open(source_image_path).convert('RGB')

    # Load other images for bleedover
    other_images = [
        Image.open(os.path.join(source_dir, fname)).convert('RGB')
        for fname in os.listdir(source_dir)
        if os.path.isfile(os.path.join(source_dir, fname))
    ]

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    print('Pre-Iteration: Posterizing')
    image = posterize(image, palette_size)

    for i in range(iterations):
        print(f'Iteration {i+1}/{iterations}')

        # Checkerboarding
        if r.getrandbits(1):
            if r.random() < 0.7:
                print('  Checkerboarding blocks')
                image = checkerboarding_blocks(image, other_images, block_count=32, block_size=32)
            else:
                print('  Checkerboarding stripes')
                image = checkerboarding_stripes(image, other_images, block_count=16, block_size=8)

        # Snow
        if r.getrandbits(1):
            if r.random() < 0.7:
                print('  Snow stripes')
                image = snow_stripes(image, 0.08)
            else:
                print('  Snow full')
                image = snow_full(image, 0.08)

        # Screen tears
        if r.getrandbits(1):
            if r.random() < 0.7:
                print('  Horizontal tear')
                image = screen_tear_horizontal(image, tear_count=6, max_offset=16, min_spacing=8)
            else:
                print('  Vertical tear')
                image = screen_tear_vertical(image, tear_count=3, max_offset=16, min_spacing=8)

    # Final color shift and sharpen
    print('Post-Iteration: Colour shift and sharpen')
    image = colour_shift(image)
    image = image.filter(ImageFilter.SHARPEN)

    # Save and show
    output_path = os.path.join(output_dir, f'glitch-v3-{image_name}')
    print(f'Exporting to {output_path}')
    image.save(output_path)
    image.show()

# -----------------------------
# Example usage
# -----------------------------
if __name__ == '__main__':
    source_dir = './Art/Source Images'
    source_image_path = os.path.join(source_dir, '07l679a8co411.jpg')
    glitch_pipeline(source_image_path, source_dir)
