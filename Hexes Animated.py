from PIL import Image, ImageDraw

UPSCALE = 2
WIDTH, HEIGHT = 1920 * UPSCALE, 1080 * UPSCALE
SCALE = 100 * UPSCALE
THIRD_SCALE = SCALE // 3
TWO_THIRD_SCALE = THIRD_SCALE * 2
HALF_SCALE = SCALE // 2
QUARTER_SCALE = SCALE // 4
THREE_QUARTER_SCALE = HALF_SCALE + QUARTER_SCALE

TOP_POINTS = [(x * SCALE, y * SCALE) for x, y in 
              ((0.25, 0.00), (0.75, 0.00), (1.00, 0.25), (0.75, 0.50), (0.25, 0.50), (0.00, 0.25))]
FRONT_POINTS = [(x * SCALE, y * SCALE) for x, y in 
                ((0.25, 0.50), (0.75, 0.50), (0.75, 2.00), (0.25, 2.00))]
LEFT_POINTS = [(x * SCALE, y * SCALE) for x, y in 
               ((0.00, 0.25), (0.25, 0.50), (0.25, 2.00), (0.00, 1.75))]
RIGHT_POINTS = [(x * SCALE, y * SCALE) for x, y in 
                ((0.75, 0.50), (1.00, 0.25), (1.00, 1.75), (0.75, 2.00))]

RIGHT_SHADING = 0.58431372549
TOP_SHADING = 0.89019607843
LEFT_SHADING = 0.84705882352
FRONT_SHADING = 0.77647058823

COLOURS = ((255, 255, 255),)
TOP_COLOURS = [tuple(int(ch * TOP_SHADING) for ch in colour) for colour in COLOURS]
FRONT_COLOURS = [tuple(int(ch * FRONT_SHADING) for ch in colour) for colour in COLOURS]
LEFT_COLOURS = [tuple(int(ch * LEFT_SHADING) for ch in colour) for colour in COLOURS]
RIGHT_COLOURS = [tuple(int(ch * RIGHT_SHADING) for ch in colour) for colour in COLOURS]

def hexe(x_off: float, y_off: float, draw: ImageDraw.ImageDraw):
    draw.polygon([(x + x_off, y + y_off) for x, y in LEFT_POINTS], LEFT_COLOURS[0])
    draw.polygon([(x + x_off, y + y_off) for x, y in RIGHT_POINTS], RIGHT_COLOURS[0])
    draw.polygon([(x + x_off, y + y_off) for x, y in FRONT_POINTS], FRONT_COLOURS[0])
    draw.polygon([(x + x_off, y + y_off) for x, y in TOP_POINTS], TOP_COLOURS[0])
    
image = Image.new('RGB', (WIDTH, HEIGHT), (0, 0, 0))
draw = ImageDraw.Draw(image)    
    
for y in range(-151, HEIGHT, 300):
    for x in range(0, WIDTH, 302):
        hexe(x, y, draw)
        
    for x in range(-151, WIDTH, 302):
        hexe(x, y + 150, draw)

image.resize((WIDTH // UPSCALE, HEIGHT // UPSCALE), Image.LANCZOS)
image.show()