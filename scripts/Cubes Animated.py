import math
from PIL import Image, ImageDraw

# --- Configuration ---
UPSCALE = 2
WIDTH, HEIGHT = 1920 * UPSCALE, 1080 * UPSCALE
SCALE = 100 * UPSCALE
HALF_SCALE = SCALE // 2
QUARTER_SCALE = SCALE // 4
THREE_QUARTER_SCALE = HALF_SCALE + QUARTER_SCALE

TOP_POINTS = [(x * SCALE, y * SCALE) for x, y in ((0.5, 0.0), (0.0, 0.25), (0.5, 0.5), (1.0, 0.25))]
LEFT_POINTS = [(x * SCALE, y * SCALE) for x, y in ((0.0, 0.25), (0.0, 1.75), (0.5, 2.0), (0.5, 0.5))]
RIGHT_POINTS = [(x * SCALE, y * SCALE) for x, y in ((0.5, 0.5), (0.5, 2.0), (1.0, 1.75), (1.0, 0.25))]

TOP_SHADING = 0.95294117647
LEFT_SHADING = 0.58039215686
RIGHT_SHADING = 0.80000000000

COLOURS = ((214, 2, 112), (0, 56, 168))
TOP_COLOURS = [tuple(ch * TOP_SHADING for ch in colour) for colour in COLOURS]
LEFT_COLOURS = [tuple(ch * LEFT_SHADING for ch in colour) for colour in COLOURS]
RIGHT_COLOURS = [tuple(ch * RIGHT_SHADING for ch in colour) for colour in COLOURS]

# --- Animation settings ---
FPS = 30
DURATION = 4  # seconds
NUM_FRAMES = FPS * DURATION

AMPLITUDE = HALF_SCALE  # maximum vertical displacement
WAVELENGTH = 150        # controls wave length across cubes

def inv_lerp(a: float, b: float, v: float):
    return (v - a) / (b - a)

def lerp(a: float, b: float, t: float):
    return int(a + (b - a) * t)

def ping_pong(x, L=1):
    return L - abs((x % 2 * L) - L)

def lerp_colour(a: tuple[float], b: tuple[float], t: float):
    return tuple(lerp(a_c, b_c, t) for a_c, b_c in zip(a, b))

# --- Cube drawing function ---
def cube(x_off: float, y_off: float, y_displacement, draw: ImageDraw.ImageDraw):
    yn = inv_lerp(-AMPLITUDE, AMPLITUDE, y_displacement)
    c_off = ping_pong(x_off + yn)
    
    draw.polygon([(x + x_off, y + y_off) for x, y in LEFT_POINTS], lerp_colour(LEFT_COLOURS[0], LEFT_COLOURS[1], c_off))
    draw.polygon([(x + x_off, y + y_off) for x, y in RIGHT_POINTS], lerp_colour(RIGHT_COLOURS[0], RIGHT_COLOURS[1], c_off))
    draw.polygon([(x + x_off, y + y_off) for x, y in TOP_POINTS], lerp_colour(TOP_COLOURS[0], TOP_COLOURS[1], c_off))

# --- Generate frames ---
frames = []
for frame_idx in range(NUM_FRAMES):
    # Normalized time for seamless loop (0 → 2π)
    t = 2 * math.pi * frame_idx / NUM_FRAMES

    image = Image.new('RGB', (WIDTH, HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    for y in range(-SCALE, HEIGHT, SCALE + HALF_SCALE):
        for x in range(0, WIDTH, SCALE):
            offset = math.sin((x / WAVELENGTH) + (y / WAVELENGTH) + t) * AMPLITUDE
            cube(x, y + offset, offset, draw)

        for x in range(-HALF_SCALE, WIDTH, SCALE):
            offset = math.sin((x / WAVELENGTH + 0.5) + (y / WAVELENGTH + 0.5) + t) * AMPLITUDE
            cube(x, y + THREE_QUARTER_SCALE + offset, offset, draw)

    # Downscale for anti-aliasing
    frame = image.resize((WIDTH // UPSCALE, HEIGHT // UPSCALE), Image.LANCZOS)
    frames.append(frame)

# --- Save as GIF ---
print("Saving GIF")

frames[0].save(
    r'.\Art\Generated Gifs\isometric_wave.gif',
    save_all=True,
    append_images=frames[1:],
    duration=1000 // FPS,  # milliseconds per frame
    loop=0
)

print("GIF saved as isometric_wave.gif")