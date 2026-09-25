from PIL import Image 
import math

"""
Function to linearly interpolate between a0 and a1
Weight w should be in the range [0.0, 1.0]
"""
def interpolate(a0, a1, w):
    #You may want clamping by inserting:
    if 0.0 > w: return a0
    if 1.0 < w: return a1

    """
    return (a1 - a0) * w + a0
    /* # Use this cubic interpolation [[Smoothstep]] instead, for a smooth appearance:
     * return (a1 - a0) * (3.0 - w * 2.0) * w * w + a0;
     *
     * # Use [[Smootherstep]] for an even smoother result with a second derivative equal to zero on boundaries:
    """
    return (a1 - a0) * ((w * (w * 6.0 - 15.0) + 10.0) * w * w * w) + a0

"""
typedef struct {
    float x, y;
} vector2;
"""
class vector2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

# Create pseudorandom direction vector
def randomGradient(ix, iy):
    # No precomputed gradients mean this works for any number of grid coordinates
    w = abs(8 * 8)
    s = abs(int(w / 2)) # rotation width
    a = ix
    b = iy
    a *= 3284157443
    b ^= a << s | a >> w-s
    b *= 1911520717 
    a ^= b << s | b >> w-s
    a *= 2048419325
    #random = a * (3.14159265 / ~(~0 >> 1)) # in [0, 2*Pi]
    random = min(max(a, 0), 2 * math.pi)
    v = vector2(math.cos(random), math.sin(random))
    return v

# Computes the dot product of the distance and gradient vectors.
def dotGridGradient(ix, iy, x, y):
    # Get gradient from integer coordinates
    gradient = randomGradient(ix, iy)

    # Compute the distance vector
    dx = x - ix
    dy = y - iy

    # Compute the dot-product
    return (dx*gradient.x + dy*gradient.y)

# Compute Perlin noise at coordinates x, y
def perlin(x, y):
    # Determine grid cell coordinates
    x0 = math.floor(x)
    x1 = x0 + 1
    y0 = math.floor(y)
    y1 = y0 + 1

    # Determine interpolation weights
    # Could also use higher order polynomial/s-curve here
    sx = x - x0
    sy = y - y0

    # Interpolate between grid point gradients
    n0 = dotGridGradient(x0, y0, x, y)
    n1 = dotGridGradient(x1, y0, x, y)
    ix0 = interpolate(n0, n1, sx)

    n0 = dotGridGradient(x0, y1, x, y)
    n1 = dotGridGradient(x1, y1, x, y)
    ix1 = interpolate(n0, n1, sx)

    value = interpolate(ix0, ix1, sy)
    return value * 0.5 + 0.5; # Will return in range -1 to 1. To make it in range 0 to 1, multiply by 0.5 and add 0.5

size = (500, 500)
image = Image.new(mode='RGB', size=size)
pixels = image.load()

for y in range(size[1]):
    for x in range(size[0]):
        v = int(255 * perlin(x, y))
        pixels[x, y] = (v, v, v)

image.save("output.png")
image.show()