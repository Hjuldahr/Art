import os
from PIL import Image

SOURCE_DIR = 'Source Images'
OUTPUT_DIR = 'Generated Gifs'

def raster_scan_between(img1, img2):
    width, height = img1.size
    pixels1 = img1.load()
    pixels2 = img2.load()

    frames = [img1.copy()]

    for parity in (0, 1):  # 0 = even rows, 1 = odd rows
        print(parity)
        for y in range(parity, height, 2):
            # Replace entire row
            for x in range(width):
                pixels1[x, y] = pixels2[x, y]

            frames.append(img1.copy())

    return frames

parent_dir = os.path.dirname(__file__)
source_dir = os.path.join(parent_dir, SOURCE_DIR)
output_dir = os.path.join(parent_dir, OUTPUT_DIR)
os.makedirs(output_dir, exist_ok=True)

file_name_1 = 'artworks-JPoVuXDmFWCLhyVS-oysneg-t1080x1080.jpg'
file_name_2 = 'artworks-JPoVuXDmFWCLhyVS-oysneg-t1080x1080-reversed.jpg'

image_1 = Image.open(os.path.join(source_dir, file_name_1)).convert("RGB")
image_2 = Image.open(os.path.join(source_dir, file_name_2)).convert("RGB")

image_1 = image_1.resize((image_1.size[0] // 3, image_1.size[1] // 3), Image.NEAREST)
image_2 = image_2.resize((image_2.size[0] // 3, image_2.size[1] // 3), Image.NEAREST)

frames = raster_scan_between(image_2, image_1)
print('exporting')
# 10s
frames[0].save(os.path.join(output_dir, f'raster-scanning.gif'), save_all=True, append_images=frames[1:], duration=1000 / image_1.size[1], loop=1)
print('done')