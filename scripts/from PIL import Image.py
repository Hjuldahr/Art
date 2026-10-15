from PIL import Image

image = Image.open('C:\\Users\\robert\\Documents\\VS Code Files\\Art\\Source Images\\DSF5682.jpg')
pixels = image.load()
width, height = image.size
deltas= {}

for y in range(height):
    for x in range(width):
        this = pixels[x, y]
        deltas = [
            tuple((c1 - c2) for c1, c2 in zip(this, pixels[x, (y - 1) % height])),
            tuple((c1 - c2) for c1, c2 in zip(this, pixels[x, (y + 1) % height])),
            tuple((c1 - c2) for c1, c2 in zip(this, pixels[(x - 1) % width, y])),
            tuple((c1 - c2) for c1, c2 in zip(this, pixels[(x + 1) % width, y]))
        ]
        

image.show()