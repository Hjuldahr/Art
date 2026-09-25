import math
import random
import colorsys
from PIL import Image, ImageDraw

# Constants
COLOUR_PALLETTE = [
    (255,0,0),
    (255,255,0),
    (0,255,0),
    (0,255,255),
    (0,0,255),
    (255,0,255)
]

A = (83-16, 250)
B = (417+16, 345) #TEMP hack, y should be 250
WIDTH, HEIGHT = 500, 500
SIZE = (WIDTH, HEIGHT)

FRAME_COUNT = 240          # total frames in the gif
BUBBLE_COUNT = 18          # number of bubbles in the stream
ARC_HEIGHT = 90            # vertical displacement amplitude
SIZE_BASE = 1             # smallest bubble radius
SIZE_VAR = 22              # random variance for max middle size

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))

def looping_t(raw_t):
    """Return a 0..1 modulo value for seamless looping."""
    return (raw_t % 1.0)

def pingpong(x, L):
    return L - abs((x % (2*L))-L)

def draw_portal_pair(t: float, draw: ImageDraw.ImageDraw):
    H_STEP = 6
    h_start = 0
    h_end = 167
    V_STEP = 12
    v_start = 0
    v_end = 500
    RECESS = 1

    colour_1 = None
    colour_2 = None

    for i in range(19):
        if i % 2 == 0:
            h_start += H_STEP
            colour_2 = (0,0,0)
            
            colour_1 = (0,0,0)
            
        else:
            h_end -= H_STEP
            
            n = ((i / 7) + t) % 1
            colour_1 = tuple(int(255 * c) for c in colorsys.hsv_to_rgb(n, 1, 1))
            
            c = 128 if random.random() < 0.01 else 255
            colour_2 = (c, c, c)
        
        draw.ellipse([(h_start, v_start), (h_end, v_end)], colour_1)
        draw.ellipse([(WIDTH - h_end, v_start), (WIDTH - h_start, v_end)], colour_2) 
        
        v_start += V_STEP
        v_end -= V_STEP
        h_end -= RECESS
        
def draw_bubbles(positions: list[list[list[float,float,float],float,list[int,int,int]]], draw: ImageDraw.ImageDraw):
    # Format (x, y, z, radius, colour), z=0 is first to be drawn (back_most)
    for (point, radius, colour) in positions:
        draw.circle(point[:3], radius, colour)

# TODO Make y traversal less uniform / sine like (more random at the center like a cloud). Fix disconnect from point B (not fully converging)
# Size should lerp between 0 (start) -> max_size (at center) -> 0 (start)
def make_frames() -> list[Image.Image]:
    # Pre-assign random bubble traits so their behaviour is deterministic per bubble
    bubbles = []
    for _ in range(BUBBLE_COUNT):
        spawn_offset = random.random()          # stagger appearance
        colour = random.choice(COLOUR_PALLETTE)
        max_size = SIZE_BASE + random.random() * SIZE_VAR
        vertical_offset = random.uniform(-1, 1) * ARC_HEIGHT  # random cloud-like offset
        bubbles.append({
            "offset": spawn_offset,
            "colour_a": colour,
            "colour_b": (255,255,255),
            "max_size": max_size,
            "vert_offset": vertical_offset
        })

    frames = []

    for frame_index in range(FRAME_COUNT):
        img = Image.new("RGB", SIZE, 0)
        draw = ImageDraw.Draw(img)

        points = []
        global_t = looping_t(frame_index / FRAME_COUNT)
        
        draw_portal_pair(global_t, draw)

        for b in bubbles:
            # local bubble time in 0..1
            t = looping_t(global_t - b["offset"])

            # Horizontal interpolation
            x = lerp(A[0], B[0], t)

            # Vertical arc: up toward center then back down, plus random offset
            arc = (1 - math.cos(t * math.pi)) * 0.5
            y = lerp(A[1], B[1], t) - arc * ARC_HEIGHT + b["vert_offset"] * math.sin(t * math.pi)

            # Radius: small → max → small
            if t < 0.45:
                r = lerp(SIZE_BASE, b["max_size"], t * 2)
            elif t > 0.55:
                r = lerp(b["max_size"], SIZE_BASE, (t - 0.55) * 2)
            else:
                r = b["max_size"]

            # Colour: original → greyscale with quadratic ease-out
            fade_start = 0.5
            fade_end = 0.95
            if t < fade_start:
                colour = b["colour_a"]
            else:
                c_t = (t - fade_start) / (fade_end - fade_start)
                c_t = max(0.0, min(1.0, c_t))  # clamp 0..1
                c_t = 1 - (1 - c_t) ** 2      # quadratic ease-out
                colour = lerp_color(b["colour_a"], (255,255,255), c_t)

            # z = t (makes early bubbles behind, later in front)
            z = t
            points.append(((x, y, z), r, colour))

        # Sort by z so draw_bubbles draws backmost first
        points.sort(key=lambda p: p[0][2])

        draw_bubbles(points, draw)
        frames.append(img)

    return frames

duration = 30
frames = make_frames()
frames[0].save(
    r'.\Art\Generated Gifs\Conformity.gif', 
    save_all=True, 
    append_images=frames[1:], 
    optimize=True, 
    duration=1000 / len(frames), 
    loop=0)
print('Done')