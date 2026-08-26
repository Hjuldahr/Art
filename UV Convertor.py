#https://www.reddit.com/r/UVPhotography/comments/1ne7qv4/imitating_the_uv_look_by_specifically_filtering/ 
import os
from PIL import Image

#BLUE_VIOLETE = (138, 43, 226)
#TURQUOISE = (64, 224, 208)
#RED = (255, 0, 0)
BLUE_VIOLETE_MASK = (0,   0,   255)
TURQUOISE_MASK    = (0,   255, 255)
RED_MASK          = (255, 0,   0)
MASKS = (BLUE_VIOLETE_MASK, TURQUOISE_MASK, RED_MASK)

def safe_div(v1, v2):
    """Divide safely, avoiding division by zero."""
    return 0 if v2 == 0 else v1 / v2

def filter_pixel(pixel: tuple[int, int, int]):   
    """
    Apply multiple RGB masks to a single pixel.
    
    Returns a tuple (R, G, B) representing the filtered pixel.
    Each channel is averaged across the masks and clamped to 0-255.
    """
    # Collect per-channel contributions
    result = [
        [safe_div(p, m) for m in channel_masks]
        for p, channel_masks in zip(pixel, zip(*MASKS))
    ]
    
    # Average each channel across masks, scale, and clamp
    filtered_pixel = tuple(
        int(min(255, 255 * (sum(channel) / len(channel))))
        for channel in result
    )
    
    return filtered_pixel

def filter_image(image):
    width, height = image.size
    pixels = image.load()
    new_image = Image.new(image.mode, image.size, 0)
    new_pixels = new_image.load()
    
    for y in range(height):
        print(y, height)
        for x in range(width):
            new_pixels[x, y] = filter_pixel(pixels[x, y])
            
    return new_image
            
img_name = '1000_F_243187392_wdOh1s1JMOqJYCCarpssvBar5ITBoRIb.jpg'

file_type = img_name.split('.', 1)[1]
main_path = os.path.dirname(__file__)
source_path = os.path.join(main_path, 'Source Images', img_name)
output_path = os.path.join(main_path, 'Generated Images', f'UV-{img_name}')

image = Image.open(source_path, 'r')
new_image = filter_image(image)
new_image.save(output_path, new_image.format)
new_image.show()