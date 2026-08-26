import random
from PIL import Image, ImageSequence

def axis_check(v, min_v, max_v) -> int:
    return min_v <= v <= max_v

def bound_check(x, y, min_x, min_y, max_x, max_y) -> int:
    return axis_check(x, min_x, max_x) and axis_check(y, min_y, max_y)

def random_bool() -> bool:
    return bool(random.getrandbits(1))

def first_frame(size):
    new_frame = Image.new("L", size, 0)
    width, height = size
    img_pixels = new_frame.load()
    
    for y in range(height):
        for x in range(width):
            img_pixels[x, y] = random.randrange(255)
            
    return new_frame

def transform(previous_frame, mask_frame, speed=4):
    mask_pixels = mask_frame.load()
    width, height = mask_frame.size
    
    new_frame = previous_frame.copy()
    img_pixels = new_frame.load()
    
    for y in range(height):
        for x in range(width):
            mask_pixel = mask_pixels[x, y]
            if mask_pixel > 0:
                img_pixel = img_pixels[x, y]
                img_pixel = (img_pixel + mask_pixel // speed) % 256
                img_pixels[x, y] = img_pixel
                
    return new_frame

gif = Image.open("./Source Images/apple.gif")
frames = [first_frame(gif.size)]
durations = [gif.info["duration"]]

for frame in ImageSequence.Iterator(gif):
    # Reset base to transparent each frame
    base = Image.new("RGBA", gif.size, (0, 0, 0, 0))
    rgba = frame.convert("RGBA")
    base.paste(rgba, (0, 0), rgba)
    gray = base.convert("L")
    frames.append(transform(frames[-1], gray, 4))
    durations.append(frame.info["duration"])

frames[0].save("./Generated Gifs/snow_apple.gif", save_all=True, append_images=frames[1:], optimize=False, duration=durations, loop=0)
print('done')