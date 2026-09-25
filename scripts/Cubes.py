from PIL import Image, ImageDraw

UPSCALE = 2
HEIGHT = 1080 * UPSCALE
WIDTH = 1920 * UPSCALE
SCALE = 100 * UPSCALE

HALF_SCALE = SCALE // 2
QUARTER_SCALE = SCALE // 4
THREE_QUARTER_SCALE = HALF_SCALE + QUARTER_SCALE

TOP_POINTS = [
    (0.5, 0.0), (0.0, 0.25), (0.5, 0.5), (1.0, 0.25)
]
TOP_COLOUR = (243, 243, 243)
LEFT_POINTS = [
    (0.0, 0.25), (0.0, 0.75), (0.5, 1.0), (0.5, 0.5)
]
LEFT_COLOUR = (148, 148, 148)
RIGHT_POINTS = [
    (0.5, 0.5), (0.5, 1.0), (1.0, 0.75), (1.0, 0.25)
]
RIGHT_COLOUR = (204, 204, 204)

def cube(x_off: float, y_off: float, scale: float, draw: ImageDraw.ImageDraw):
    draw.polygon([(x * scale + x_off, y * scale + y_off) for (x, y) in TOP_POINTS], TOP_COLOUR)
    draw.polygon([(x * scale + x_off, y * scale + y_off) for (x, y) in LEFT_POINTS], LEFT_COLOUR)
    draw.polygon([(x * scale + x_off, y * scale + y_off) for (x, y) in RIGHT_POINTS], RIGHT_COLOUR)

image = Image.new('RGB', (WIDTH, HEIGHT), (255,255,255))
draw = ImageDraw.Draw(image)

for y in range(-QUARTER_SCALE, HEIGHT, SCALE + HALF_SCALE):
    for x in range(0, WIDTH, SCALE):
        cube(x, y, SCALE, draw)
        
    for x in range(-HALF_SCALE, WIDTH, SCALE):
        cube(x, y + THREE_QUARTER_SCALE, SCALE, draw)

image = image.resize((WIDTH // UPSCALE, HEIGHT // UPSCALE), Image.LANCZOS)
image.show()