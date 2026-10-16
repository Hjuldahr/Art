import math
from PIL import Image, ImageEnhance, ImageFilter

def get_gradient_magnitude(this: tuple[int], right: tuple[int], down: tuple[int]) -> tuple[int]:
    output = []
    for i in range(3):  # Loop through R, G, B channels
        # Calculate individual directional differences
        dx = right[i] - this[i]
        dy = down[i] - this[i]
        
        # Calculate Euclidean distance (hypotenuse)
        #magnitude = math.sqrt(dx**2 + dy**2)
        magnitude = math.hypot(dx, dy)
        
        # Scale up slightly if edges are too dim, then clamp to 255
        output.append(min(max(0, int(magnitude)), 255))
        
    return tuple(output)

# --- Your image loading setup ---
#path = 'C:\\Users\\robert\\Documents\\VS Code Files\\Art\\Source Images\\DSF5682.jpg'
#path = 'C:\\Users\\robert\\Documents\\VS Code Files\\Art\\Source Images\\Chateaulin_1.jpg'
path = 'C:\\Users\\robert\\Documents\\VS Code Files\\Art\\Source Images\\classical-art-inspiration.png'
image = Image.open(path).convert('RGB')

image = image.filter(ImageFilter.GaussianBlur(1.25))

pixels = image.load()
width, height = image.size

new_image = Image.new('RGB', image.size, 0)
new_pixels = new_image.load()

# Generate edges using Euclidean distance
for y in range(height):
    for x in range(width):
        this_pixel = pixels[x, y]
        right_pixel = pixels[(x + 1) % width, y]
        down_pixel = pixels[x, (y + 1) % height]
        
        new_pixels[x, y] = get_gradient_magnitude(this_pixel, right_pixel, down_pixel)

new_image = ImageEnhance.Brightness(new_image).enhance(1.5)

print("Finished Generating Euclidean Edges")
new_image.show()