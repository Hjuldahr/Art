from PIL import Image

def rgb_delta(rgb_1: tuple[int], rgb_2: tuple[int]) -> tuple[int]:
    return (
        rgb_1[0] - rgb_2[0],
        rgb_1[1] - rgb_2[1],
        rgb_1[2] - rgb_2[2],
    )
    

    
def delta_average(deltas: tuple[tuple[int]]) -> tuple[int]:
    return (
        min(max(0, ((deltas[0][0] + deltas[1][0] + deltas[2][0] + deltas[3][0]) // 4) * 4), 255),
        min(max(0, ((deltas[0][1] + deltas[1][1] + deltas[2][1] + deltas[3][1]) // 4) * 4), 255),
        min(max(0, ((deltas[0][2] + deltas[1][2] + deltas[2][2] + deltas[3][2]) // 4) * 4), 255),
    )

image = Image.open('C:\\Users\\robert\\Documents\\VS Code Files\\Art\\Source Images\\DSF5682.jpg').convert('RGB')
pixels = image.load()
width, height = image.size
deltas= {}

for y in range(height):
    for x in range(width):
        this = pixels[x, y]
        deltas[x, y] = (
            rgb_delta(this, pixels[(x + 1) % width, y]),
            rgb_delta(this, pixels[x, (y - 1) % height]),
            rgb_delta(this, pixels[(x - 1) % width, y]),
            rgb_delta(this, pixels[x, (y + 1) % height])
        )
print("Finished scanning")
        
new_image = Image.new('RGB', image.size, 0)
new_pixels = new_image.load()

for y in range(height):
    for x in range(width):
        new_pixels[x, y] = delta_average(deltas[x, y])
print("Finished Generating")

new_image.show()