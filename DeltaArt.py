from PIL import Image

def drop(x, to=5):
    return (x // to) * to

def remap_range(OldValue, OldMin, OldMax, NewMin, NewMax):
    return (((OldValue - OldMin) * (NewMax - NewMin)) / (OldMax - OldMin)) + NewMin

def slow_shift(value, old_value, max_value):
    delta = value - old_value
    if delta == 0:
        return old_value
    if delta > 0:
        return min(old_value + 1, max_value)
    if delta < 0:
        return max(old_value - 1, 0)

def colour_to_wave(src_image: Image, wave_height=8):
    src_image = src_image.convert("L")
    width, height = src_image.size
    src_pixels = src_image.load()
    
    height = drop(height, wave_height)
    out_image = Image.new('L', (width, height), 0)
    out_pixels = out_image.load()
    prev_value = 0
    
    for y1 in range(0, height, wave_height):
        for x1 in range(0, width):
            value = 0
            for y2 in range(y1, y1 + wave_height):
                value += src_pixels[x1, y2]
                
            value = int(remap_range(value / wave_height, 0, 255, 0, wave_height))
            value = wave_height - value - 1
            
            if value != prev_value:
                for y2 in range(y1 + min(value, prev_value), y1 + max(value, prev_value) + 1):
                    out_pixels[x1, y2] = 255
            
            prev_value = value
            
    return out_image
    
def colour_to_rgb_wave(src_image: Image, wave_height=8):
    src_image = src_image.convert("RGB")
    width, height = src_image.size
    src_pixels = src_image.load()
    
    height = drop(height, wave_height)
    out_image = Image.new('RGB', (width, height), 0)
    out_pixels = out_image.load()
    prev_values = (0, 0, 0)
    
    for y1 in range(0, height, wave_height):
        for x1 in range(0, width):
            rgb = [0, 0, 0]
            for y2 in range(y1, y1 + wave_height):
                rgb = [v1 + v2 for v1, v2 in zip(rgb, src_pixels[x1, y2])]

            colours = [[0,0,0] for _ in range(wave_height)]

            for i, z in enumerate(zip(rgb, prev_values)):
                v1, v2 = z
                v1 = int(remap_range(v1 / wave_height, 0, 255, 0, wave_height))
                v1 = wave_height - v1 - 1
                rgb[i] = v1
                
                for j in range(min(v1, v2), max(v1, v2) + 1):
                    colours[j][i] = 255

            if rgb != prev_values:
                for i in range(wave_height):
                    out_pixels[x1, y1 + i] = tuple(colours[i])
            
            prev_values = rgb
            
    return out_image
    
src_image = Image.open("./Art/Source Images/79avborlpyh61-ezgif.jpg")
out_image = colour_to_rgb_wave(src_image, 10)
out_image.save("./Art/Generated Images/dt_79avborlpyh61-ezgif.jpg")
out_image.show()