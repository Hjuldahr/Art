from PIL import Image
import random
from colorsys import hsv_to_rgb

global colours

def denormalize_rgb(rgb):
    return tuple(int(255 * c) for c in rgb)

def generate_colours():
    h = random.uniform(0.0, 1.0)
    s = random.uniform(0.3, 0.6)
    v = random.uniform(0.3, 0.6)

    i = 1 if random.getrandbits(1) == 1 else -1
    i2 = 1 if random.getrandbits(1) == 1 else -1
    
    colours = {'bground':  denormalize_rgb(hsv_to_rgb(h, s, v)),
               'fgroundX': denormalize_rgb(hsv_to_rgb((h + 0.3) % 1, (s + 0.25 * i) % 1, (v + 0.25 * i2) % 1)), 
               'fgroundY': denormalize_rgb(hsv_to_rgb((h - 0.3) % 1, (s - 0.25 * i) % 1, (v - 0.25 * i2) % 1))}
    
    return colours

def generate_grid(pixels, width, height):
    global colours
    
    toggled_x = False
    
    for y in range(0, height):
        #if bool(random.getrandbits(1)):
        if random.random() < 0.25:
            toggled_x = not toggled_x
        
        if toggled_x:
            for x in range(0, width):
                pixels[x, y] = colours["fgroundY"]
        
    #toggled_x = False
    active = False
    prev_active = False
               
    for x in range(0, width):
        prev_active = active
        #active = bool(random.getrandbits(1))
        if random.random() < 0.25:
            active = not active
        
        if active: 
            if prev_active != active:
                toggled_x = not toggled_x
            
            toggled_y = toggled_x
            
            for y in range(0, height):
                if pixels[x, y] == colours["bground"] and y < height -1 and pixels[x, y] != pixels[x, y + 1]:
                    toggled_y = not toggled_y
                
                if toggled_y or pixels[x, y] == colours["bground"]:
                    pixels[x, y] = colours["fgroundX"]
    
    return pixels

if __name__ == '__main__':
    width = 720
    height = 720
    count = 15

    for i in range(1, count + 1):
        colours = generate_colours()
        image = Image.new('RGB', (width, height), colours["bground"])
        pixels = image.load()
        
        pixels = generate_grid(pixels, width, height)
        
        image.save(f'Art\\Generated_Images\\Grid_Art_{i}.png')
        print(i)