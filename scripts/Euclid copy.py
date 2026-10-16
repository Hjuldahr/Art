import random
from PIL import Image

def reverse_stripe(pixels, origin, vertical, canvas_width, canvas_height):
    if vertical:
        for y in range(canvas_height):
            rgb = pixels[origin, y] 
            pixels[origin, y] = (255 - rgb[0], 255 - rgb[1], 255 - rgb[2])

    else:
        for x in range(canvas_width):
            rgb = pixels[x, origin] 
            pixels[x, origin] = (255 - rgb[0], 255 - rgb[1], 255 - rgb[2])

def filter_stripe(pixels, channel, origin, vertical, canvas_width, canvas_height):
    if vertical:
        for y in range(canvas_height):
            v = pixels[origin, y][channel] 
            pixels[origin, y] = (v, v, v)

    else:
        for x in range(canvas_width):
            v = pixels[x, origin][channel] 
            pixels[x, origin] = (v, v, v)

def greyscale_stripe(pixels, origin, vertical, canvas_width, canvas_height):
    if vertical:
        for y in range(canvas_height):
            rgb = pixels[origin, y]
            v = int(rgb[0] * 0.299 + rgb[1] * 0.587 + rgb[2] * 0.114)
            pixels[origin, y] = (v, v, v)

    else:
        for x in range(canvas_width):
            rgb = pixels[x, origin]
            v = int(rgb[0] * 0.299 + rgb[1] * 0.587 + rgb[2] * 0.114)
            pixels[x, origin] = (v, v, v)

def backward_stripe(pixels, origin, vertical, canvas_width, canvas_height):
    if vertical:
        for y in range(canvas_height):
            pixels[origin, y], pixels[origin, canvas_height - y - 1] = pixels[origin, canvas_height - y - 1], pixels[origin, y]

    else:
        for x in range(canvas_width):
            pixels[x, origin], pixels[canvas_width - x - 1, origin] = pixels[canvas_width - x - 1, origin], pixels[x, origin]

def reverse_rectange(pixels, x_origin, y_origin, width, height, canvas_width, canvas_height):
    x1 = max(0, x_origin)
    y1 = max(0, y_origin)
    x2 = min(x_origin + width, canvas_width)
    y2 = min(y_origin + height, canvas_height)
    
    for y in range(y1, y2):
        for x in range(x1, x2):
            rgb = pixels[x, y]
            pixels[x, y] = (255 - rgb[0], 255 - rgb[1], 255 - rgb[2])

def filter_rectange(pixels, channel, x_origin, y_origin, width, height, canvas_width, canvas_height):
    x1 = max(0, x_origin)
    y1 = max(0, y_origin)
    x2 = min(x_origin + width, canvas_width)
    y2 = min(y_origin + height, canvas_height)
    
    for y in range(y1, y2):
        for x in range(x1, x2):
            v = pixels[x, y][channel]
            pixels[x, y] = (v, v, v)
            
def greyscale_rectange(pixels, x_origin, y_origin, width, height, canvas_width, canvas_height):
    x1 = max(0, x_origin)
    y1 = max(0, y_origin)
    x2 = min(x_origin + width, canvas_width)
    y2 = min(y_origin + height, canvas_height)
    
    for y in range(y1, y2):
        for x in range(x1, x2):
            rgb = pixels[x, y]
            v = int(rgb[0] * 0.299 + rgb[1] * 0.587 + rgb[2] * 0.114)
            pixels[x, y] = (v, v, v)

def snow(pixels, density, canvas_width, canvas_height):
    for _ in range(int(canvas_width * canvas_height * density)):
        x, y, v = random.randrange(canvas_width), random.randrange(canvas_height), random.randrange(256)
        pixels[x, y] = (v, v, v)

def snow_line(pixels, density, vertical, canvas_width, canvas_height):
    if vertical:
        for x in range(canvas_width):
            if random.random() > density:
                continue
            
            for y in range(canvas_height):
                if random.random() > 0.1:
                    continue
                
                v = random.randrange(256)
                pixels[x, y] = (v, v, v)
    else:
        for y in range(canvas_height):
            if random.random() > density:
                continue
            
            for x in range(canvas_width):
                if random.random() > 0.1:
                    continue
                
                v = random.randrange(256)
                pixels[x, y] = (v, v, v)

def colour_shift(pixels, canvas_width, canvas_height):
    directions = [random.choice([(-1, 0), (1, 0), (0, -1), (0, 1)]) for _ in range(3)]
    
    new_pixels = [[[0, 0, 0] for _ in range(canvas_width)] for _ in range(canvas_height)]
    
    for y in range(canvas_height):
        for x in range(canvas_width):
            rgb = pixels[x, y]
            for channel in range(3):
                xd, yd = directions[channel]
                new_pixels[(y + yd) % canvas_height][(x + xd) % canvas_width][channel] = rgb[channel]
    
    for y in range(canvas_height):
        for x in range(canvas_width):
            pixels[x, y] = tuple(new_pixels[y][x])

# --- Your image loading setup ---
#path = 'C:\\Users\\robert\\Documents\\VS Code Files\\Art\\Source Images\\DSF5682.jpg'
#path = 'C:\\Users\\robert\\Documents\\VS Code Files\\Art\\Source Images\\Chateaulin_1.jpg'
path = 'C:\\Users\\robert\\Documents\\VS Code Files\\Art\\Source Images\\classical-art-inspiration.png'
image = Image.open(path).convert('RGB')

pixels = image.load()
canvas_width, canvas_height = image.size

choices = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}

x_origins = set([x for x in range(0, canvas_width, 2)])
y_origins = set([y for y in range(0, canvas_height, 2)])

for i in range(32):
    print(i, end=' ')
    block_size = random.choice((16, 32, 64, 128, 256))
    vertical = random.random() < 0.5
    effect = random.choice(tuple(choices))
    
    if effect == 0:
        print('greyscale')
        greyscale_rectange(
            pixels, 
            random.randrange(0, canvas_width, block_size), random.randrange(0, canvas_height, block_size),
            block_size, block_size,
            canvas_width, canvas_height
        )
    elif effect == 1:
        print('reverse')
        reverse_rectange(
            pixels, 
            random.randrange(0, canvas_width, block_size), random.randrange(0, canvas_height, block_size),
            block_size, block_size,
            canvas_width, canvas_height
        )
    elif effect == 2:
        print('filter')
        filter_rectange(
            pixels, random.randrange(3),
            random.randrange(0, canvas_width, block_size), random.randrange(0, canvas_height, block_size),
            block_size, block_size,
            canvas_width, canvas_height
        )
    elif effect == 3:
        choices.discard(3)
        print('snow')
        snow(
            pixels, 0.04,
            canvas_width, canvas_height
        )  
    elif effect == 4:
        choices.discard(4)
        print('snow line')
        snow_line(
            pixels, 0.04, vertical,
            canvas_width, canvas_height
        ) 
    elif effect == 5:
        choices.discard(5)
        print('shift')
        colour_shift(pixels, canvas_width, canvas_height)
        
    elif effect == 6:
        choices.discard(6)
        print('greyscale line')
        
        if vertical:
            origin = random.choice(list(x_origins))
            x_origins.discard(origin)
        else:
            origin = random.choice(list(y_origins))
            y_origins.discard(origin)
        
        greyscale_stripe(
            pixels, origin, vertical,
            canvas_width, canvas_height
        )
    elif effect == 7:
        choices.discard(7)
        print('reverse line')
        
        if vertical:
            origin = random.choice(list(x_origins))
            x_origins.discard(origin)
        else:
            origin = random.choice(list(y_origins))
            y_origins.discard(origin)
        
        reverse_stripe(
            pixels, origin, vertical,
            canvas_width, canvas_height        
        )
    elif effect == 8:
        choices.discard(8)
        print('filter line')
        
        if vertical:
            origin = random.choice(list(x_origins))
            x_origins.discard(origin)
        else:
            origin = random.choice(list(y_origins))
            y_origins.discard(origin)
        
        filter_stripe(
            pixels, random.randrange(3), origin, vertical,
            canvas_width, canvas_height     
        )
    elif effect == 9:
        choices.discard(9)
        print('backward line')
        
        if vertical:
            origin = random.choice(list(x_origins))
            x_origins.discard(origin)
        else:
            origin = random.choice(list(y_origins))
            y_origins.discard(origin)
        
        backward_stripe(
            pixels, origin, vertical,
            canvas_width, canvas_height     
        )
        
if 3 in choices:
    print('end snow')
    snow(pixels, 0.01, canvas_width, canvas_height)  
    
if 5 in choices:
    print('end shift')
    colour_shift(pixels, canvas_width, canvas_height)

print("Finished Generating")
image.show()

# Todo tearing, rectangle rotate (clockwise, anticlockwise 90), rectangle mirror (x, y axis), rectangle swap (between 2)