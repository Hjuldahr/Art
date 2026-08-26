from PIL import Image

global OFFSET, SCALE, SIZE, pixelMap, MAXDEPTH, WHITE, BLACK

def fractal(x=0, y=0, depth=0):
    global OFFSET, SCALE, pixelMap, MAXDEPTH, BLACK 

    if depth < MAXDEPTH:
        if (depth % 2 == 0):
            fractal(x / 2.0 + 1.0 * SCALE, y / 2.0,                       depth + 1) #0
            fractal(x / 2.0 - 0.5 * SCALE, y / 2.0 + 0.866025404 * SCALE, depth + 1) #120
            fractal(x / 2.0 - 0.5 * SCALE, y / 2.0 - 0.866025404 * SCALE, depth + 1) #240
        else:
            fractal(x / 2.0 + 0.5 * SCALE, y / 2.0 + 0.866025404 * SCALE, depth + 1) #60
            fractal(x / 2.0 - 1.0 * SCALE, y / 2.0,                       depth + 1) #180
            fractal(x / 2.0 + 0.5 * SCALE, y / 2.0 - 0.866025404 * SCALE, depth + 1) #300

    pixelMap[round(x + OFFSET), round(y + OFFSET)] = BLACK

MAXDEPTH = 16
SIZE = 10000 
SCALE = SIZE * 0.25
OFFSET = round(SIZE / 2)
BLACK = (0,0,0)
WHITE = (255,255,255)

img = Image.new(mode='RGB', size=(SIZE, SIZE), color=WHITE)
pixelMap = img.load() 

fractal()

print ("done")

img.save('Generated Images/Fractal.png', format='PNG')
img.show()