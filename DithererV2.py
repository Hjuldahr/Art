import math
import os
import random
from PIL import Image
import numpy as np
#import imageio

#def save_as_mp4(frames, out_path, fps=30):
#    frames_np = [np.array(f) for f in frames]
#    imageio.mimsave(out_path, frames_np, fps=fps, codec="libx264", quality=8)

def rgb_to_visual_cmyk(r, g, b):
    c = (g + b) // 2
    m = (r + b) // 2
    y = (r + g) // 2
    k = (r + g + b) // 3
    return c, m, y, k

def rgb_to_l(r, g, b):
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def calculate_population(width, height, pixels):
    return tuple((x, y) for y in range(height) for x in range(width) if pixels[x, y] != (0, 0, 0))

def calculate_weights(width, height, pixels):
    return tuple((rgb_to_l(*pixels[x,y]) / 255) ** 2 for y in range(height) for x in range(width) if pixels[x, y] != (0, 0, 0))

def calculate_dynamic_weights(width, height, pixels, upper = 2, duration = 50):
    increment = upper / duration
    luminosities = tuple(rgb_to_l(*pixels[x,y]) / 255 for y in range(height) for x in range(width) if pixels[x, y] != (0, 0, 0))
    weights = tuple(tuple(luminosity ** (increment * t) for luminosity in luminosities) for t in range(duration + 1))
    return weights

def merge(old, new, factor = 1.75):
    return tuple(int((c1 + c2) / factor) for c1, c2 in zip(old, new))

def ping_pong(t, length):
    return int(length - abs((t % (2.0 * length)) - length))

def process_prisma(in_path, out_path, block_size = 5):
    old_image = Image.open(in_path)
    width, height = old_image.size
    old_pixels = old_image.convert('RGB').load()
    
    layers = {k: Image.new('RGB', (width, height), 0) for k in ('R','G','B','C','M','Y','K')}
    layers_pixels = {k: v.load() for k, v in layers.items()}
    
    half_block_size = block_size // 2
    blocks_per_layer = round((width * height) / (block_size**2))
    
    for y_pos in range(height):
        for x_pos in range(width):
            r, g, b = old_pixels[x_pos, y_pos]
            c, m, y, k = rgb_to_visual_cmyk(r, g, b)
            
            layers_pixels['R'][x_pos, y_pos] = (r, 0, 0)
            layers_pixels['G'][x_pos, y_pos] = (0, g, 0)
            layers_pixels['B'][x_pos, y_pos] = (0, 0, b)
            layers_pixels['C'][x_pos, y_pos] = (0, c, c)
            layers_pixels['M'][x_pos, y_pos] = (m, 0, m)
            layers_pixels['Y'][x_pos, y_pos] = (y, y, 0)
            layers_pixels['K'][x_pos, y_pos] = (k, k, k)

    new_image = Image.new('RGB', (width, height), 0)
    new_pixels = new_image.load()

    points = calculate_population(width, height, old_pixels)
    weights = calculate_weights(width, height, old_pixels)
    for layer_pixels in layers_pixels.values():
        next_points = random.choices(population=points, weights=weights, k=blocks_per_layer)
        for point in next_points:
            x0, y0 = point
            colour = layer_pixels[x0, y0]
            for y1 in range(y0-half_block_size, y0+half_block_size+1):
                for x1 in range(x0-half_block_size, x0+half_block_size+1):
                    if 0 <= x1 < width and 0 <= y1 < height:
                        new_pixels[x1, y1] = merge(new_pixels[x1, y1], colour)

    new_image.save(out_path)

def process_sampling(in_path, out_path, block_size = 5):
    old_image = Image.open(in_path)
    width, height = old_image.size
    old_pixels = old_image.convert('RGB').load()
    
    new_image = Image.new('RGB', (width, height), 0)
    new_pixels = new_image.load()
    
    half_block_size = block_size // 2
    blocks = round((width * height) / (block_size**2))

    for point in random.choices(population=calculate_population(width, height, old_pixels), weights=calculate_weights(width, height, old_pixels), k=blocks):
        x0, y0 = point
        colour = old_pixels[x0, y0]
        for y1 in range(y0-half_block_size, y0+half_block_size+1):
            for x1 in range(x0-half_block_size, x0+half_block_size+1):
                if 0 <= x1 < width and 0 <= y1 < height:
                    new_pixels[x1, y1] = merge(new_pixels[x1, y1], colour)
        
    new_image.save(out_path)

def process_sampling_gif(in_path, out_path, block_size = 5, iterations = 100, sub_cycles = 2, gif_length = 120):
    sub_cycles = math.ceil(sub_cycles / 2) * 2
    
    old_image = Image.open(in_path)
    width, height = old_image.size
    old_pixels = old_image.convert('RGB').load()

    frames = []
    
    half_block_size = block_size // 2
    blocks = round((width * height) / (block_size**2))
    print("Calculating Valid Points")
    population = calculate_population(width, height, old_pixels)
    print("Calculating Weights")
    weights = calculate_dynamic_weights(width, height, old_pixels, 2, iterations // sub_cycles)
    ping_pong_limit = len(weights) - 1
    print("Generating Animation")
    for t in range(iterations):
        print(f'{t / iterations:%}')

        frame = Image.new('RGB', (width, height), 0)
        frame_pixels = frame.load()
        
        for point in random.choices(population=population, weights=weights[ping_pong(t, ping_pong_limit)], k=blocks):
            x0, y0 = point
            colour = old_pixels[x0, y0]
            for y1 in range(y0-half_block_size, y0+half_block_size+1):
                for x1 in range(x0-half_block_size, x0+half_block_size+1):
                    if 0 <= x1 < width and 0 <= y1 < height:
                        frame_pixels[x1, y1] = merge(frame_pixels[x1, y1], colour)
        
        frames.append(frame)
        
    frames[0].save(out_path, save_all=True, append_images=frames[1:], optimize=False, duration=gif_length / iterations, loop=0)

def process_blackwall_gif(in_path, out_path, block_size = 5, iterations = 100, sub_cycles = 2):
    sub_cycles = math.ceil(sub_cycles / 2) * 2
    
    old_image = Image.open(in_path)
    width, height = old_image.size
    old_pixels = old_image.convert('RGB').load()

    frames = []
    
    half_block_size = block_size // 2
    blocks = round((width * height) / ((block_size**2) * 3))
    print("Calculating Valid Points")
    population = calculate_population(width, height, old_pixels)
    print("Calculating Weights")
    weights = calculate_dynamic_weights(width, height, old_pixels, 2, iterations // sub_cycles)
    ping_pong_limit = len(weights) - 1
    print("Generating Animation")
    for t in range(iterations):
        print(f'{t / iterations:.0%}')

        frame = Image.new('RGB', (width, height), 0)
        frame_pixels = frame.load()
        
        #Blue
        for point in random.choices(population=population, weights=weights[ping_pong(t, ping_pong_limit)], k=blocks):
            x0, y0 = point
            _, _, b = old_pixels[x0, y0]
            colour = (0, 0, b)

            for y1 in range(y0-half_block_size, y0+half_block_size+1):
                for x1 in range(x0-half_block_size, x0+half_block_size+1):
                    if 0 <= x1 < width and 0 <= y1 < height:
                        frame_pixels[x1, y1] = colour
        
        #Magenta
        for point in random.choices(population=population, weights=weights[ping_pong(t, ping_pong_limit)], k=blocks):
            x0, y0 = point
            r, _, b = old_pixels[x0, y0]
            m = (r + b) // 2
            colour = (m, 0, m)

            for y1 in range(y0-half_block_size, y0+half_block_size+1):
                for x1 in range(x0-half_block_size, x0+half_block_size+1):
                    if 0 <= x1 < width and 0 <= y1 < height:
                        frame_pixels[x1, y1] = colour
                        
        #Red
        for point in random.choices(population=population, weights=weights[ping_pong(t, ping_pong_limit)], k=blocks):
            x0, y0 = point
            r, _, _ = old_pixels[x0, y0]
            colour = (r, 0, 0)

            for y1 in range(y0-half_block_size, y0+half_block_size+1):
                for x1 in range(x0-half_block_size, x0+half_block_size+1):
                    if 0 <= x1 < width and 0 <= y1 < height:
                        frame_pixels[x1, y1] = colour
        
        frames.append(frame)
        
    #frames[0].save(out_path, save_all=True, append_images=frames[1:], optimize=True, duration=gif_length / iterations, loop=0)
    #save_as_mp4(frames, out_path)

if __name__ == '__main__':
    file_name = 'sample_2.gif'
    
    main_path = os.path.dirname(__file__)
    in_path = os.path.join(main_path, 'Source Images', file_name)
    out_path = os.path.join(main_path, 'Generated Gifs', f'dithered-{file_name.split(".", 1)[0]}.gif')
    
    #process_sampling_gif(in_path, out_path)
    #process_blackwall_gif(in_path, out_path, 5, 50)
    print('Done')