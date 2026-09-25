from PIL import Image

filename = 'colour-wheel-aspinall-creative-564.jpg'

image = Image.open(f'Source Images\\{filename}', mode='r')
pixels = image.load() 
width, height = image.size

for x in range(width):
    for y in range(height):
        rgb = pixels[x, y]
        rgb = (255 - rgb[0], 255 - rgb[1], 255 - rgb[2])
        pixels[x, y] = rgb

print("saving")
image.save(f'Generated Images\\{filename}')
print("done")
image.show()
image.close()