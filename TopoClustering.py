from PIL import Image

def calculate_pixel_noise(pixel: tuple[int, int, int]):
    return sum(pixel) #temporary placeholder

def process(image, epsilon):
    fourth_epsilon = epsilon * 4
    width, height = image.size
    pixels = image.load()

    noise_values = [[calculate_pixel_noise(pixels[x, y]) for x in range(width)] for y in range(height)]

    new_image = Image.new('RGB', (width, height), 0)
    new_pixels = new_image.load()
    
    peaks = [(x, y) for y in range(height) for x in range(width) if noise_values[y][x] >= fourth_epsilon]
                
    i = 0
    coords = []
    for peak in peaks:
        coords.append(peak)
        
        while i < len(coords):
            if i % 1000 == 0:
                print(i, len(coords))
            x, y = coords[i]
            
            if x > 1 and noise_values[y][x-1] > epsilon and (x-1, y) not in coords:
                coords.append((x-1, y))
                
            if x < width - 1 and noise_values[y][x+1] > epsilon and (x+1, y) not in coords:
                coords.append((x+1, y))
                
            if y > 1 and noise_values[y-1][x] > epsilon and (x, y-1) not in coords:
                coords.append((x, y-1))
                
            if y < height - 1 and noise_values[y+1][x] > epsilon and (x, y+1) not in coords:
                coords.append((x, y+1))
                
            i += 1

    for coord in coords:
        x, y = coord
        value = noise_values[y][x]
        if value > fourth_epsilon:
            new_pixels[x, y] = (255, 0, 0)
        elif value > epsilon:
            new_pixels[x, y] = (255, 165, 0)
    
    return new_image

image = Image.open('./Art/Alt Source Images/image.jpg')
new_image = process(image, 150)
new_image.save('./Art/Generated Images/image.jpg')