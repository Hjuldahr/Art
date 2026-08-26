import os
import random
from PIL import Image, ImageDraw

SOURCE_NAME = 'classical-art-inspiration-v0-2yw9cgy01h5f1.png'
SOURCE_DIR = 'Source Images'
OUTPUT_DIR = 'Generated Images'
FAIL_THRESHOLD = 100
MAX_BACKOFF = 100

def initial_state(size: tuple[int, int], colours, lines=100) -> list[list[tuple[int, int]]]:
    width, height = size
    line_points = []
    
    usable_colours = colours[:]
    while len(usable_colours) < lines:
        usable_colours.extend(colours[:])
        
    usable_colours = random.sample(usable_colours, k=lines)
    
    for usable_colour in usable_colours:
        """
        point_pairs = [random_colour(), random.randrange(width), random.randrange(height), random.randrange(width), random.randrange(height)]
        
        for side in random.sample((0, 1, 2, 3), k=2):
            match(side):
                case 0:
                    point_pairs.append((random.randrange(width), 0))
                case 1:
                    point_pairs.append((width-1, random.randrange(height)))
                case 2:
                    point_pairs.append((random.randrange(width), height-1))
                case 3:
                    point_pairs.append((0, random.randrange(height)))

        line_points.append(point_pairs)
        """
        line_points.append([usable_colour, 
                            (random.randrange(width), random.randrange(height)), 
                            (random.randrange(width), random.randrange(height))])
    return line_points

def mutate(size: tuple[int, int], line_data, d):
    width, height = size
    
    for i in range(len(line_data)):
        rgb, (x1, y1), (x2, y2) = line_data[i]
        
        x1 = (x1 + random.randint(-d, d)) % width
        x2 = (x2 + random.randint(-d, d)) % width
        y1 = (y1 + random.randint(-d, d)) % height
        y2 = (y2 + random.randint(-d, d)) % height
        
        line_data[i] = rgb, (x1, y1), (x2, y2)
        
    return line_data

def find_brightness(r, g, b):
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def similiarity_test(image_A: Image.Image, image_B: Image.Image) -> int:
    """
    Pixelwise image comparison.\n
    Requires the images to have the same size.\n
    A return of zero indicates a perfect match.

    Args:
        image_A (Image.Image): First Image
        image_B (Image.Image): Second Image

    Returns:
        int: Number of mismatched RGB pixel values. 
    """
    width, height = image_A.size
    pixels_A = image_A.load()
    pixels_B = image_B.load()
    difference = 0
    
    for y in range(height):
        for x in range(width):
            rgb_A = pixels_A[x, y]
            rgb_B = pixels_B[x, y]
            difference += 1 if rgb_A[0] != rgb_B[0] else 0
            difference += 1 if rgb_A[1] != rgb_B[1] else 0
            difference += 1 if rgb_A[2] != rgb_B[2] else 0
                
    return difference

def anneal(reference_image: Image.Image, target_likeness = 100, max_iterations = 1000) -> Image.Image:
    old_image = None
    
    pixels = reference_image.load()
    colours = set()
    for y in range(reference_image.size[1]):
        for x in range(reference_image.size[0]):
            rgb = pixels[x, y]
            colours.add(rgb)
                
    dimmest = sorted(colours, key=lambda e: find_brightness(*e))[0]
    colours = list(colours)
    
    old_image = Image.new(reference_image.mode, reference_image.size, dimmest)
    draw = ImageDraw.Draw(old_image)
    
    prev_line_data = initial_state(reference_image.size, colours, reference_image.size[0] * reference_image.size[1])
    for line in prev_line_data:
        draw.line(line[1:], line[0])  

    fails = 0
    back_off = 0
    
    try:
        prev_score = similiarity_test(reference_image, old_image)
        print(-1, "score", prev_score)
        
        for i in range(max_iterations):
            new_image = Image.new(reference_image.mode, reference_image.size, dimmest)
            draw = ImageDraw.Draw(new_image)
            
            new_line_data = mutate(reference_image.size, prev_line_data, 1 + back_off)
            for line in new_line_data:
                draw.line(line[1:], line[0])  
            
            next_score = similiarity_test(reference_image, new_image)
            
            old_image = new_image.copy()
            
            if next_score <= target_likeness:
                break
            
            elif next_score <= prev_score + back_off * 10:
                prev_score = next_score
                prev_line_data = new_line_data[:]
                print(i, "score", prev_score)
                back_off = 0
                fails = 0
                
            else:
                fails += 1 
                
                if fails > FAIL_THRESHOLD:
                    back_off = min(back_off + 1, MAX_BACKOFF)  
                    print(i, "backoff", back_off)
                    fails = 0
                
    except KeyboardInterrupt:
        print("Early Stop")
    except Exception as e:
        print(e)
    finally:
        return old_image.copy()

# Reconstructs from uniquelly coloured straight line segments sampled from image
if __name__ == '__main__':
    parent_dir = os.path.dirname(__file__)
    input_path = os.path.join(parent_dir, SOURCE_DIR, SOURCE_NAME)
    output_path = os.path.join(parent_dir, OUTPUT_DIR, SOURCE_NAME.replace('.', '-annealed.'))
    
    input_image = Image.open(input_path).convert('RGB')
    output_image = anneal(input_image, 5000, 1000000)
    
    if output_image is not None:
        output_image.save(output_path)
        output_image.show()