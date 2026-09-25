from pathlib import Path
import random
from PIL import Image, ImageSequence

BLACK = (0,0,0)

def calculate_population(width: int, height: int, pixels: "Image.PixelAccess") -> tuple[tuple[int,int]]:
    return tuple(
        (x, y) 
        for y in range(height) 
        for x in range(width) 
        if pixels[x, y] != BLACK
    )

def rgb_to_l(r: int, g: int, b: int) -> float:
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def calculate_weights(width: int, height: int, pixels: "Image.PixelAccess") -> tuple[float]:
    return tuple(
        (rgb_to_l(*pixels[x,y]) / 255) ** 2 
        for y in range(height) 
        for x in range(width) 
        if pixels[x, y] != BLACK
    )

def merge(old, new, factor = 1.75):
    return tuple(
        int((c1 + c2) / factor) 
        for c1, c2 
        in zip(old, new)
    )

def process_sampling_gif(in_path: Path, out_path: Path, block_size: int = 5):
    gif = Image.open(in_path, mode='r')
    new_frame_durations = []
    new_frames = []
    
    half_block_size = block_size // 2
    block_count = round((gif.width * gif.height) / (block_size**2))

    for frame in ImageSequence.Iterator(gif):
        frame = frame.convert('RGB')
        frame_pixels = frame.load()
        
        new_frame = Image.new('RGB', frame.size, BLACK)
        new_frame_pixels = new_frame.load()
        
        frame_population = calculate_population(*frame.size, frame_pixels)
        frame_weights = calculate_weights(*frame.size, frame_pixels)
        
        for (x0, y0) in random.choices(frame_population, frame_weights, k=block_count):
            colour = frame_pixels[x0, y0]
            
            for y1 in range(y0-half_block_size, y0+half_block_size+1):
                for x1 in range(x0-half_block_size, x0+half_block_size+1):
                    if 0 <= x1 < frame.width and 0 <= y1 < frame.height:
                        new_frame_pixels[x1, y1] = merge(new_frame_pixels[x1, y1], colour)
        
        new_frames.append(new_frame)
        new_frame_durations.append(frame.info['duration'])
        
    new_frames[0].save(
        out_path, save_all=True, append_images=new_frames[1:], optimize=False, duration=new_frame_durations, loop=0
    )
    
def random_glitch_colour(glitch_type_2_colour: tuple[int,int,int]):
    glitch_type = random.choices([0,1,2,3,4], weights=[20,20,25,15,10], k=1)[0]
    
    if glitch_type == 0: # Null write
        return (0,0,0)
    elif glitch_type == 1: # Saturation
        return(255,255,255)
    elif glitch_type == 2: # Structured corruption
        return glitch_type_2_colour
    elif glitch_type == 3: # Bit collapse
        v = random.randint(0, 255)
        return (v,v,v)
    elif glitch_type == 4: # Channel fault
        pix = [0,0,0]
        pix[random.randint(0,2)] = random.randint(0,255)
        return tuple(pix) 
    
def process_sampling_gif_glitched(in_path: Path, out_path: Path, block_size: int = 5, colour_glitching: float = 0.125, pixel_sticking: float = 0.0625):
    glitch_colours = ((255,255,0),(255,0,255),(0,255,255))
    
    gif = Image.open(in_path, mode='r')
    new_frame_durations = []
    new_frames = []
    
    previous_frame_pixels = None

    for n, frame in enumerate(ImageSequence.Iterator(gif)):
        print(n)
        
        random_block_size = block_size + random.randint(-1,1)
        random_half_block_size = random_block_size // 2
        block_count = round((frame.width * frame.height) / (random_block_size**2))

        glitch_type_2_colour = random.choice(glitch_colours)
        factor = random.uniform(1.6, 2.1)
        
        frame = frame.convert('RGB')
        frame_pixels = frame.load()
        
        new_frame = Image.new('RGB', frame.size, BLACK)
        new_frame_pixels = new_frame.load()
        
        frame_population = calculate_population(*frame.size, frame_pixels)
        frame_population = tuple((i, p) for i, p in enumerate(frame_population))
        frame_weights = calculate_weights(*frame.size, frame_pixels)
        
        for i, (x0, y0) in random.choices(frame_population, frame_weights, k=block_count):
            weight = frame_weights[i]
            
            if random.random() < colour_glitching * weight:
                block_colour = random_glitch_colour(glitch_type_2_colour)
            else:
                block_colour = frame_pixels[x0, y0]
            
            for y1 in range(y0-random_half_block_size, y0+random_half_block_size+1):
                for x1 in range(x0-random_half_block_size, x0+random_half_block_size+1):
                    if 0 <= x1 < frame.width and 0 <= y1 < frame.height:
                        if random.random() < pixel_sticking * weight and n > 1:
                            new_frame_pixels[x1, y1] = previous_frame_pixels[x1, y1]
                        else:
                            new_frame_pixels[x1, y1] = merge(new_frame_pixels[x1, y1], block_colour, factor)
        
        new_frames.append(new_frame)
        new_frame_durations.append(frame.info['duration'])
        
        previous_frame_pixels = new_frame_pixels
        
    new_frames[0].save(
        out_path, save_all=True, append_images=new_frames[1:], optimize=False, duration=new_frame_durations, loop=0
    )
    
if __name__ == '__main__':
    root_path = Path(__file__).resolve().parent
    in_file = '22e49430a9a271ca1eaef7ea89ddd858.gif'

    in_path = root_path / 'Source Images' / in_file
    out_path = root_path / 'Generated Gifs' / f'glitched_dithered_neo_{in_file}'

    process_sampling_gif_glitched(in_path, out_path, 3)
    print('done!')