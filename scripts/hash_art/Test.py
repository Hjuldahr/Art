from PIL import Image

def spiral_traverse(height, width):
    top = 0
    bottom = height - 1
    left = 0
    right = width - 1

    while top <= bottom and left <= right:
        for col in range(left, right + 1):
            yield top, col
        top += 1

        for row in range(top, bottom + 1):
            yield row, right
        right -= 1

        if top <= bottom:
            for col in range(right, left - 1, -1):
                yield bottom, col
            bottom -= 1

        if left <= right:
            for row in range(bottom, top - 1, -1):
                yield row, left
            left += 1
    
width = 100
height = 125

img = Image.new('L', (width, height), 255)
pixels = img.load()

for n, (y, x) in enumerate(spiral_traverse(height, width)):
    pixels[x, y] = 255 - abs((n % (2 * 255)) - 255)
    
img.show()