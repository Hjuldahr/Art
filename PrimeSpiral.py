import colorsys
from pathlib import Path
import uuid
from PIL import Image

def pingPong(t, length):
    return length - abs((t % (2 * length)) - length)

def prime_color(n, cycle=360):
    hue = pingPong(n, cycle) / cycle
    saturation = 1.0
    value = 0.6 + 0.4 * ((n % 17) / 16)  # subtle brightness shift
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
    return int(r * 255), int(g * 255), int(b * 255)

def generate_prime_sieve(limit):
    sieve = [True] * (limit + 1)
    sieve[0:2] = [False, False]
    for i in range(2, int(limit ** 0.5) + 1):
        if sieve[i]:
            for j in range(i*i, limit + 1, i):
                sieve[j] = False
    return tuple(sieve)

def spiral(width, height):
    # Force odd dimensions for perfect centering
    width += width % 2 == 0
    height += height % 2 == 0
    
    image = Image.new('RGB', (width, height), (0, 0, 0))
    pixels = image.load()

    originX = width // 2
    originY = height // 2
    
    x, y = 0, 0       # position relative to center
    index = 1         # offset to exclude element 0 / number 0

    max_steps = width * height
    sieve = generate_prime_sieve(max_steps)  # extra padding

    steps_in_leg = 1
    leg_count = 0  # increments after each leg
    
    deltas = ((1, 0), (0, 1), (-1, 0), (0, -1))
    
    while index <= max_steps:
        # directions cycle: right(0), down(1), left(2), up(3)
        direction = leg_count % 4
        
        dx, dy = deltas[direction]
        
        for _ in range(steps_in_leg):
            offsetX = originX + x
            offsetY = originY + y
            
            if 0 <= offsetX < width and 0 <= offsetY < height and sieve[index]:
                pixels[offsetX, offsetY] = prime_color(index)
            
            x += dx
            y += dy
            index += 1
            
            if index > max_steps:
                break
        
        leg_count += 1
        # Increase step length every two legs
        if leg_count % 2 == 0:
            steps_in_leg += 1

    output_dir = Path('Generated Images')
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f'spiral_{width}x{height}_{uuid.uuid4().hex}.png'
    image.save(output_file)
    print(f"Saved spiral image to {output_file}")

if __name__ == '__main__':
    spiral(6400, 6400)
