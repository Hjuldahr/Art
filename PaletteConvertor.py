import numpy as np
from PIL import Image

def lerp_rgb(rgb1, rgb2, t):
    return tuple(int((1-t)*c1 + t*c2) for c1, c2 in zip(rgb1, rgb2))

def gradient_lookup(palette, t):
    """Map t in [0,1] into palette sequence smoothly."""
    n = len(palette)
    if n == 1:
        return palette[0]
    # Which segment?
    pos = t * (n-1)
    i = int(pos)
    if i >= n-1:
        return palette[-1]
    local_t = pos - i
    return lerp_rgb(palette[i], palette[i+1], local_t)

def recolour_image(original_img, palette):
    arr = np.array(original_img.convert("RGB"), dtype=np.uint8)
    h, w, _ = arr.shape

    # Convert to grayscale [0,1] for indexing into palette
    luminance = arr.mean(axis=2) / 255.0

    # Flatten for easier mapping
    flat = luminance.flatten()
    recolored = np.array([gradient_lookup(palette, t) for t in flat], dtype=np.uint8)

    return Image.fromarray(recolored.reshape(h, w, 3), "RGB")

def hex_to_rgb(palette):
    new_pallete = []
    for colour in palette:
        colour = colour.removeprefix('#')
        new_pallete.append((int(colour[:2], 16), int(colour[2:4], 16), int(colour[4:6], 16)))
    return new_pallete

# Example
#palette = [(211,85,255), (255,0,244), (124,0,255), (9,0,255), (4,0,105)]
palette = ['#000000ff', '#32066Aff', '#7F1F82ff', '#DA446Aff', '#FDA06Cff', '#FBFCC0ff'] #magma

file_name = 'Moraine-Lake-1.png'
palette_name = 'magma'

file_name, file_type = file_name.split('.', 1)
palette = hex_to_rgb(palette)
original_img = Image.open(f"./Art/Source Images/{file_name}.{file_type}").convert("RGB")
new_image = recolour_image(original_img, palette)
new_image.save(f"./Art/Generated Images/{file_name}_{palette_name}.{file_type}")
new_image.show()
