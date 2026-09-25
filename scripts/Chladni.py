#0=a*sin(pi*n*x)*sin(pi*m*y)+b*sin(pi*m*x)*sin(pi*n*y)

global a, m, n, b, scale, size, lineMin, lineMax

import random as r
import numpy as np
from PIL import Image

a = 1
n = 7
m = 2
b = -1

size = 1000
lineWidth = 0.05

lineMin = 128 * (1 - lineWidth)
lineMax = 128 * (1 + lineWidth)

def generateFrame(a, b, n, m, scale, color):
    global size, lineMin, lineMax

    # Create a grid of x and y values
    x = np.linspace(0, 1, size)  # x values from 0 to 1
    y = np.linspace(0, 1, size)  # y values from 0 to 1
    X, Y = np.meshgrid(x, y)

    # Calculate the left-hand side of the equation
    Z = a * np.sin(np.pi * n * X) * np.sin(np.pi * m * Y) + b * np.sin(np.pi * m * X) * np.sin(np.pi * n * Y)

    # Normalize Z to [0, 255] for image display
    Z_normalized = (((Z - Z.min()) / (Z.max() - Z.min())) * 255 * scale).astype(np.uint8)

    # Create an image from the normalized array
    image = Image.fromarray(Z_normalized, mode='L')  # 'L' mode for grayscale
    image = image.convert("RGB")  # Convert to RGB for coloring

    # Color the image based on the zero crossings
    pixels = image.load()
    for i in range(size):
        for j in range(size):
            if Z_normalized[j, i] > lineMin and Z_normalized[j, i] < lineMax: #0-255
                pixels[i, j] = color
            #elif Z_normalized[j, i] > r.randrange(64, 128) and Z_normalized[j, i] < r.randrange(128, 192):
            #    pixels[i, j] = color
            else:
                pixels[i, j] = (0, 0, 0)

    return image


def generateFrames(start, stop, step):
    frames = []
    
    scale = start
    while scale <= stop:
        print (f"{scale}/{stop}")

        r = int(255 * (1 - (scale / stop)))
        g = 0
        b = int(255 * ((scale / stop)))

        frames.append(generateFrame(1, -1, 7, 2, scale, (r,g,b)))
        scale += step

    i = 1
    while i > 0:
        print (f"{i}/1")
        r = 0
        g = 0
        b = int(255 * i)
        
        frames.append(generateFrame(1, -1, 7, 2, stop, (r,g,b))) 
        i -= 0.125

    print("done")

    return frames

def generateGif(path, start, stop, step):
    frames = generateFrames(start, stop, step)
    frames[0].save(f"{path}.gif", save_all=True, append_images=frames[1:], optimize=True, duration=len(frames), loop=0)

generateGif("Generated Images/Chladni7", 0, 8, 0.015625) #1,16,0.25

#generateFrame(1, 1, 2, 7, (255,255,255)).save("Generated Images/Chladni1.png")
#print("done")