from PIL import Image

def calculateBrightness(pixel):
    return (0.299 * pixel[0] * pixel[0] + 0.587 * pixel[1] * pixel[1] + 0.114 * pixel[2] * pixel[2]) ** 0.5

def recolour_gradient(pixels, size, thickness):
    width, height = size
    
    y1 = height
    delta = (0.125 * height) / 1365
    scale = thickness
    
    intScale = int(scale)
    previousIntScale = intScale
    
    while y1 > 0:
        x1 = 0
        yEnd = min(y1 + intScale, height)
        
        while x1 < width:
            xEnd = min(x1 + intScale, width)
            
            for y2 in range(y1, yEnd):
                for x2 in range(x1, xEnd):
                    value = int(calculateBrightness(pixels[x2, y2]))
                    pixels[x2, y2] = (value, value, value)
            
            x1 += intScale + thickness
            
        scale += delta
        intScale = max(int(scale), thickness)
        
        if intScale != previousIntScale:
            previousIntScale = intScale
            for x2 in range(0, width):
                pixels[x2, y1] = (0, 0, 0)
                    
        y1 -= intScale + thickness
        
def recolour_dots(pixels, size, density):
    width, height = size
    
    for y in range(height):
        for x in range(width):
            if x % density > 0 or y % density > 0:
                value = int(calculateBrightness(pixels[x, y]))
                pixels[x, y] = (value, value, value)
                
def recolour_grid(pixels, size, spacing, thickness):
    width, height = size
    
    for y1 in range(0, height, spacing + thickness):
        yEnd = min(y1 + spacing, height)
        for x1 in range(0, width, spacing + thickness):
            xEnd = min(x1 + spacing, width)
            for y2 in range(y1, yEnd):
                for x2 in range(x1, xEnd):
                    value = int(calculateBrightness(pixels[x2, y2]))
                    pixels[x2, y2] = (value, value, value)

#testing min colour density needed for colourizing full images
if __name__ == '__main__':
    fileName = 'tree'
    fileType = 'jpg'
        
    print("Reading Source Image")
    image = Image.open(f'Source Images\\{fileName}.{fileType}', mode='r').convert('RGB')
    pixels = image.load()
    size = image.size
    
    #print(f"Processing Gradient Image")
    #recolour_gradient(image.load(), image.size)
    #image.save(f'Generated Images\\{fileName}_recoloured_gradient.png')
    
    #print("Processing Grid Image")
    #recolour_grid(pixels, size, 8, 2)
    #image.save(f'Generated Images\\{fileName}_grid.png')
    
    print("Processing Gradient Image")
    recolour_gradient(pixels, size, 2)
    image.save(f'Generated Images\\{fileName}_gradient.png')