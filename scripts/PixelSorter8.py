from math import floor
import os
from colorsys import hsv_to_rgb, rgb_to_hsv
from PIL import Image

FILENAME = '360_F_369634160_Pv5jIedHbMhEoCeaL4GwXYky3Ij0QY1f.jpg'

parent_path = os.path.join(os.path.dirname(__file__))
IN_PATH = os.path.join(parent_path, 'Source Images', FILENAME)
OUT_PATH = os.path.join(parent_path, 'Generated Gifs', FILENAME.split('.')[0] + '_pixelsorted.gif')

os.makedirs(os.path.dirname(IN_PATH), exist_ok=True)
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

FPS = 10
DURATION = 10  # seconds
NUM_FRAMES = FPS * DURATION

def normalize(colour: tuple[int, int, int]) -> tuple[float, float, float]:
    """0-255 -> 0-1

    Args:
        colour (tuple[int, int, int]): Denormalized Colour

    Returns:
        tuple[float, float, float]: Normalized Colour
    """
    return (colour[0] / 255, colour[1] / 255, colour[2] / 255)

def denormalize(colour: tuple[float, float, float]) -> tuple[int, int, int]:
    """0-1 -> 0-255

    Args:
        colour (tuple[float, float, float]): Normalized Colour

    Returns:
        tuple[int, int, int]: Denormalized Colour
    """
    return tuple(min(max(0, int(c * 255)), 255) for c in colour)

def H_coord(d: int, w: int, h: int, x0: int = 0, y0: int = 0, dir: int = 0) -> tuple[int, int]:
    """
    H-curve distance to 2D point with orientation flipping.

    Args:
        d (int): h-curve distance
        w (int): rect width
        h (int): rect height
        x0 (int): subrect x offset
        y0 (int): subrect y offset
        dir (int): entry direction (0=→, 1=↓, 2=←, 3=↑)

    Returns:
        tuple[int,int]: point (x, y)
    """

    if w == 1 and h == 1:
        return (x0, y0)

    if w >= h:
        w1 = floor(w / 2)
        w2 = w - w1

        # Decide order of halves based on orientation
        if dir in (0, 3):  # left-to-right or top-to-left
            first_w, second_w = w1, w2
            first_x0, second_x0 = x0, x0 + w1
            first_dir, second_dir = dir, (dir + 1) % 4  # rotate for second half
        else:  # right-to-left or bottom-to-right
            first_w, second_w = w2, w1
            first_x0, second_x0 = x0 + w1, x0
            first_dir, second_dir = (dir + 1) % 4, dir

        if d < first_w * h:
            return H_coord(d, first_w, h, first_x0, y0, first_dir)
        else:
            return H_coord(d - first_w * h, second_w, h, second_x0, y0, second_dir)

    else:
        h1 = floor(h / 2)
        h2 = h - h1

        if dir in (0, 1):  # left-to-right or top-to-left
            first_h, second_h = h1, h2
            first_y0, second_y0 = y0, y0 + h1
            first_dir, second_dir = dir, (dir + 1) % 4
        else:  # right-to-left or bottom-to-right
            first_h, second_h = h2, h1
            first_y0, second_y0 = y0 + h1, y0
            first_dir, second_dir = (dir + 1) % 4, dir

        if d < w * first_h:
            return H_coord(d, w, first_h, x0, first_y0, first_dir)
        else:
            return H_coord(d - w * first_h, w, second_h, x0, second_y0, second_dir)

def pixel_sort(hsv_colours, points, sourceImage: Image.Image, start_h = 0.25, end_h = 1.0) -> Image.Image:
    sortedImage = sourceImage.copy()
    sortedPixels = sortedImage.load()
    
    sorting = False
    selected_points = []
    select_colours = []
    for p, hsv in zip(points, hsv_colours):
        if not sorting and hsv[0] > start_h:
            sorting = True
            
        if sorting:
            selected_points.append(p)
            select_colours.append(hsv)
            
            if hsv[0] > end_h:
                select_colours = sorted(select_colours, key=lambda hsv: hsv[0])
                
                for (x, y), hsv in zip(selected_points, select_colours):
                    rgb = denormalize(hsv_to_rgb(*hsv))
                    sortedPixels[(x, y)] = rgb
                
                selected_points = []
                select_colours = []
                sorting = False
                
    if sorting and selected_points:
        select_colours = sorted(select_colours, key=lambda hsv: hsv[0])
        
        for (x, y), hsv in zip(selected_points, select_colours):
            rgb = denormalize(hsv_to_rgb(*hsv))
            sortedPixels[(x, y)] = rgb
                
    return sortedImage

if __name__ == '__main__':
    sourceImage = Image.open(IN_PATH).convert('RGB')
    width, height = sourceImage.size
    sourcePixels = sourceImage.load()
    
    frames = []
    for frame_idx in range(NUM_FRAMES):
        f = frame_idx / NUM_FRAMES
        frame_dir = frame_idx % 4
        
        #start_h = f if f < 0.5 else 1.0 - f # Pongs  
        start_h = f # Gives breathing space
        end_h = (start_h + 0.2) % 1.0
        
        if end_h < start_h:
            v = start_h
            end_h = start_h
            end_h = v
        
        points = tuple(H_coord(d, width, height, dir=frame_dir) for d in range(width * height))
        hsv_colours = tuple(rgb_to_hsv(*normalize(sourcePixels[x, y])) for (x, y) in points)
        
        frame = pixel_sort(
            hsv_colours,
            points, 
            sourceImage, 
            start_h, 
            end_h
        )
        frames.append(frame.convert('P', palette=Image.ADAPTIVE))
        
        print(f'{f:.0%}')
    
    frames[0].save(OUT_PATH, 
        save_all=True,
        append_images=frames[1:],
        duration=1000 // FPS,  # milliseconds per frame
        loop=0
    )
    print('Done')