import math
import os
import random
from PIL import Image, ImageOps 

red = '\033[0;31m'
green = '\033[0;32m'
reset = '\033[0m'

def load_target_image(path, SCALE):
    img = Image.open(path)
    img = ImageOps.grayscale(img) #preserves more colour data by grayscaling before downscaling
    img = ImageOps.scale(img, SCALE, Image.Resampling.LANCZOS)
    return img

def place_initial_dots(width, height, point_count):
    points = {point: random.randint(1, 255) for point in random.sample([(x, y) for x in range(width) for y in range(height)], point_count)}
    return points

def compare(width, height, pixels, points):
    total_diff = 0
    for y in range(height):
        for x in range(width):
            total_diff += abs(pixels[x, y] - points.get((x, y), 0))
    return total_diff

def points_to_image(width, height, points):
    image = Image.new('L', (width, height), 0)
    pixels = image.load()
    for coord, v in points.items():
        x, y = coord
        pixels[x, y] = v
    return image

def mutate_points(width, height, points, step_size, max_change):
    next_points = {}
    
    for coord, value in points.items():
        x, y = coord
        value = (value + random.randint(-max_change, max_change)) % 256
        neighbors = list(set(
            (int(x + step_size * math.cos(math.radians(theta))) % width, int(y + step_size * math.sin(math.radians(theta))) % height)
            for theta in range(0, 360, 36)
        ))
        random.shuffle(neighbors)
        for new_coord in neighbors:
            if new_coord not in next_points:
                coord = new_coord
                break
        next_points[coord] = value
        
    return next_points

def main(file_name, scale, point_density, iterations, film_progress=True, source_dir='Source Images', output_dir = 'Generated Images'):
    parent_dir = os.path.dirname(__file__)
    source_path = os.path.join(parent_dir, source_dir, file_name)
    output_path = os.path.join(parent_dir, output_dir)
    os.makedirs(output_path, exist_ok=True) 
    output_path = os.path.join(output_path, file_name.split('.')[0])

    source_image = load_target_image(source_path, scale)
    source_pixels = source_image.load()
    width, height = source_image.size
    point_count = int(width * height * point_density)
    
    print("Placing Initial Dots")
    best_points = place_initial_dots(width, height, point_count)
    print("Comparing Initial Fit")
    best_fit = compare(width, height, source_pixels, best_points)
    print("Fitting Set")
    print(f'i: {0:>6} fit: {best_fit:>8} delta: {0:>6} iter: {0:>6} variance: inf')
    
    images = []
    
    #regressive acceptance criteria for poor results during stagnant conditiond
    current_threshold = 0
    max_threshold = 10000
    failed_iterations = 0
    fail_interval = 100
    fail_step_size = 100
    
    for i in range(1, iterations):
        step_size = max(1, int(width * 0.1 * (1 - i / iterations)))
        max_change = max(1, int(16 * (1 - i / iterations)))
        
        next_points = mutate_points(width, height, best_points, step_size, max_change)
        fit = compare(width, height, source_pixels, next_points)
        
        delta = best_fit - fit
        if delta >= current_threshold:
            if film_progress:
                images.append(points_to_image(width, height, best_points))
                if delta < 0:
                    images[-1] = ImageOps.colorize(images[-1], black="black", white="red")
            
            best_points = next_points
            print(f'i: {i:>6} fit: {fit:>8} delta: {delta:>6} iter: {failed_iterations:>6} variance: {step_size:>2}')
            best_fit = fit
            failed_iterations = 0
            current_threshold = 0
            
            if fit <= max_threshold:
                break
            
        else:
            failed_iterations += 1
            if failed_iterations % fail_interval == 0:
                current_threshold = max(current_threshold - fail_step_size, -max_threshold)
                print(f'{red}i: {i:>6} fit: {fit:>8} delta: {delta:>6} iter: {failed_iterations:>6} threshold: {current_threshold}{reset}')
        
    print("Drawing Image")        
    images.append(points_to_image(width, height, best_points))
    print(f"saving Image: {output_path}") 
    
    images[0].save(output_path + '.png')
    if film_progress:
        images[0].save(output_path + '.gif', save_all=True, append_images=images[1:], optimize=True, duration=60/iterations)

if __name__ == '__main__':
    file_name = 'Sillitoe-black-white.gif'

    scale = 0.75          # % original reduction
    point_density = 0.5  # % coverage of points
    iterations = 10000  # Number of optimization steps
    
    main(file_name, scale, point_density, iterations)