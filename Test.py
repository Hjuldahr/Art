from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance

FILENAME = 'DSF5682.jpg'

root = Path(__file__).parent
src_path = root / 'Source Images' / FILENAME
dst_path = root / 'Generated Images' / f'Test-{FILENAME}'

in_img = Image.open(src_path).convert("RGB")
width, height = in_img.size
in_pxl = in_img.load()

out_img = Image.new('RGB', in_img.size)
out_pxl = out_img.load()

for y in range(height):
    for x in range(width):
        col = in_pxl[x, y]
        out_pxl[x, y] = (hash(col) ^ hash((x, y))) & 0xFF_FF_FF
        
out_img.show()