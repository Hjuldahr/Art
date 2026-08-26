from PIL import Image

global OFFSET, SCALE, SIZE, pixelMap, MAXDEPTH, WHITE, BLACK

def fill(x0, y0, size):
    global pixelMap, BLACK, SIZE

    size /= 2

    for x in range(max(0, round(x0 - size)), min(round(x0 + size + 1), SIZE)):
        for y in range(max(0, round(y0 - size)), min(round(y0 + size + 1), SIZE)):
              pixelMap[x,y] = BLACK

def fractal(size, x=0, y=0, depth=0):
    global OFFSET, SCALE, pixelMap, MAXDEPTH, BLACK 

    if depth < MAXDEPTH:
        fractal(size / 3.0, x / 3.0,         y / 3.0 + SCALE, depth + 1) 
        fractal(size / 3.0, x / 3.0,         y / 3.0 - SCALE, depth + 1) 
        fractal(size / 3.0, x / 3.0 + SCALE, y / 3.0,         depth + 1) 
        fractal(size / 3.0, x / 3.0 - SCALE, y / 3.0,         depth + 1) 

        fractal(size / 3.0, x / 3.0 + SCALE, y / 3.0 + SCALE, depth + 1) 
        fractal(size / 3.0, x / 3.0 - SCALE, y / 3.0 - SCALE, depth + 1) 
        fractal(size / 3.0, x / 3.0 + SCALE, y / 3.0 - SCALE, depth + 1) 
        fractal(size / 3.0, x / 3.0 - SCALE, y / 3.0 + SCALE, depth + 1) 

    fill(x + OFFSET, y + OFFSET, round(size))

MAXDEPTH = 2 #16
SIZE = 10000 #10000
SCALE = SIZE / 3
OFFSET = round(SIZE / 2)
BLACK = (0,0,0)
WHITE = (255,255,255)

img = Image.new(mode='RGB', size=(SIZE, SIZE), color=WHITE)
pixelMap = img.load() 

fractal(size=SCALE)

print ("done")

img.save('Generated Images/Fractal3.png', format='PNG')