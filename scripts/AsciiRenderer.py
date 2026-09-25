from PIL import Image

def remapRange(value, oldMax, newMax):
    return min(int((value / oldMax) * newMax), newMax)

def setPixelBlock(newPixels, value, offsets, IMG_SIZE, CHAR_PIXEL_SIZE):
    x0, y0 = offsets
    x_end = min(x0 + CHAR_PIXEL_SIZE[0], IMG_SIZE[0])
    y_end = min(y0 + CHAR_PIXEL_SIZE[1], IMG_SIZE[1])
    
    for y in range(y0, y_end):
        for x in range(x0, x_end):
            newPixels[x, y] = (value, value, value)

def newBrightnessMap(values, IMG_SIZE, CHAR_PIXEL_SIZE, CHAR_PIXEL_PADDING):
    MAX_VALUE = max(max(values))
    #black background is inaccurate since the ascii has a white background, but is easier on the eyes than a white grid
    newImage = Image.new('RGB', IMG_SIZE, (0, 0, 0)) 
    newPixels = newImage.load()
    i, j = 0, 0
    
    for y in range(0, IMG_SIZE[1], CHAR_PIXEL_SIZE[1] + CHAR_PIXEL_PADDING[1]):
        for x in range(0, IMG_SIZE[0], CHAR_PIXEL_SIZE[0] + CHAR_PIXEL_PADDING[0]):
            value = values[i][j]
            value = remapRange(value, MAX_VALUE, 255)
            setPixelBlock(newPixels, value, (x, y), IMG_SIZE, CHAR_PIXEL_SIZE)
            j += 1
        i += 1
        j = 0
            
    return newImage

def imgToASCII(values, ASCII_PALETTE):
    MAX_VALUE = max(max(values))
    ASCII_PALETTE_SIZE = len(ASCII_PALETTE) - 1 #adjusts for zero based indexing
    
    asciiStr = '\n'.join(''.join(ASCII_PALETTE[remapRange(value, MAX_VALUE, ASCII_PALETTE_SIZE)] for value in row) for row in values)
    
    return asciiStr

def calculateBrightness(pixel):
    return (0.299 * pixel[0] * pixel[0] + 0.587 * pixel[1] * pixel[1] + 0.114 * pixel[2] * pixel[2]) ** 0.5

def calculateBrightnessBlock(pixels, offsets, IMG_SIZE, CHAR_PIXEL_SIZE):
    x0, y0 = offsets
    x_end = min(x0 + CHAR_PIXEL_SIZE[0], IMG_SIZE[0])
    y_end = min(y0 + CHAR_PIXEL_SIZE[1], IMG_SIZE[1])
    
    total, count = 0, 0
    for b in (calculateBrightness(pixels[x, y]) for y in range(y0, y_end) for x in range(x0, x_end)):
        total += b
        count += 1

    return total / count if count else 0

def calculateBrightnessAll(pixels, IMG_SIZE, CHAR_PIXEL_SIZE, CHAR_PIXEL_PADDING):
    #skips padding by having inner loop goes upto char size, while outer loops goes up to char size + padding size
    return [[calculateBrightnessBlock(pixels, (x, y), IMG_SIZE, CHAR_PIXEL_SIZE) 
            for x in range(0, IMG_SIZE[0], CHAR_PIXEL_SIZE[0] + CHAR_PIXEL_PADDING[0])] 
            for y in range(0, IMG_SIZE[1], CHAR_PIXEL_SIZE[1] + CHAR_PIXEL_PADDING[1])]

if __name__ == '__main__':
    #using tilemap based pixel to char mapping, so its not 1 pixel per char, but x:y pixels per char minus padding
    asciiPallete = '@%#*+=-:. '
    charSize = (8, 15)
    charPadding = (1, 1)
    
    fileName = 'tree'
    fileType = 'jpg'
    
    print("Reading Source Image")
    image = Image.open(f'Source Images\\{fileName}.{fileType}', mode='r').convert('RGB')
    pixels = image.load()
    
    print("Processing Image Brightness")
    values = calculateBrightnessAll(pixels, image.size, charSize, charPadding)
    
    print("Generating Greyscale Image")
    newImage = newBrightnessMap(values, image.size, charSize, charPadding)
    
    print("Writing Grayscale Image ")
    newImage.save(f'Generated Images\\{fileName}_shading.png')
    
    print("Generating ASCII Image")
    asciiStr = imgToASCII(values, asciiPallete)
    
    print("Writing ASCII Image")
    with open(f'Generated Images\\{fileName}5.txt', "w") as f:
        f.write(asciiStr)