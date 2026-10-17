from __future__ import annotations
import math
import random as rand
from typing import Any, Generator, Iterable, Iterator, Literal
from PIL import Image, ImageOps

GREY_PALLETE = tuple((v, v, v) for v in range(256))

# Helpers
# Colour Manipulation

type colour = tuple[int, int, int]
type channels = Literal[0, 1, 2]
type opt_channels = Literal[0, 1, 2] | None

def _RGB_filter(rgb: colour, channel: channels, /) -> colour:
    match channel:
        case 0: return (rgb[channel], 0, 0)
        case 1: return (0, rgb[channel], 0)
        case 2: return (0, 0, rgb[channel])
        case _: return rgb # No filter
        
def _RGB_to_greyscale(rgb: colour, channel: opt_channels = None, /) -> colour:
    # Channel is for artistic greyscale conversions
    if channel is None:
        i = round(rgb[0] * 0.299 + rgb[1] * 0.587 + rgb[2] * 0.114)
    else:
        i = rgb[channel]
    return GREY_PALLETE[i]

def _invert_RGB(rgb: colour) -> colour:
    return (255 - rgb[0], 255 - rgb[1], 255 - rgb[2])

# Random Colours

def randomize[T](elements: Iterable[T]) -> list[T]:
    if isinstance(elements, Generator):
        elements = tuple(elements)
        
    return rand.sample(elements, k=len(elements)) 

def _bell() -> int:
    return min(max(round(rand.gauss(127.5, 40)), 0), 255)

def _random_RGB() -> colour:
    return (_bell(), _bell(), _bell())

def _random_grey() -> colour:
    return GREY_PALLETE[_bell()]

def _random_1() -> colour:
    return GREY_PALLETE[0 if rand.random() < 0.5 else 255]

# Positions

type point = tuple[int, int]
type size = tuple[int, int]

class Quad:
    __slots__ = ('x1', 'y1', 'x2', 'y2', 'width', 'height', 'area')
    
    @classmethod
    def from_image(cls, img: Image.Image) -> Quad:
        return cls(0, 0, *img.size) 
    
    @classmethod
    def square(cls, origin: point, size: int, canvas_size: size) -> Quad:
        return cls.rect(origin, size, size, canvas_size)
        
    @classmethod
    def rect(cls, origin: point, width: int, height: int, canvas_size: size) -> Quad:
        return cls(
            min(max(origin[0], 0), canvas_size[0]),
            min(max(origin[1], 0), canvas_size[1]),
            min(max(origin[0] + width, 0), canvas_size[0]),
            min(max(origin[1] + height, 0), canvas_size[1]),
        )    
    
    def __init__(self, x1: int, y1: int, x2: int, y2: int):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self.width = x2 - x1
        self.height = y2 - y1
        self.area = self.width * self.height

    @property
    def top_left(self) -> point:
        return (self.x1, self.y1)
    
    @property
    def bottom_right(self) -> point:
        return (self.x2 - 1, self.y2 - 1)

    @property
    def corners(self) -> tuple[point, point, point, point]:
        return (
            (self.x1, self.y1), (self.x2 - 1, self.y1),
            (self.x1, self.y2 - 1), (self.x2 - 1, self.y2 - 1)
        )

    def indices(self) -> range:
        return range(self.area)
    
    def global_points(self) -> Iterator[point]:
        return ((x, y) for y in range(self.y1, self.y2) for x in range(self.x1, self.x2))

    def local_points(self) -> Iterator[point]:
        return ((x, y) for y in range(self.height) for x in range(self.width))

def _reduce_indices(indices: range, density: float, /) -> list[int] | range:
    """Best effort spatial sampling. Tip: 1/n <= density < 1 is the ideal range"""
    n = len(indices)
    
    if density <= 0.0 or n == 0:
        return []
    if density >= 1.0 or n == 1:
        return indices
    return rand.sample(indices, math.ceil(n * density))

def _materialize_points(indices: Iterable[int], quad: Quad, /) -> list[point]: 
    x, y = quad.top_left
    width = quad.width
    return [(x + i % width, y + i // width) for i in indices]

def _produce_sparse_points(quad: Quad, density: float) -> list[point]:
    return _materialize_points(
        _reduce_indices(
            quad.indices(), 
            density
        ),
        quad
    )

# Effects
# Stripes

def snow_stripe(img: Image.Image, origin: int, /, is_vertical: bool, density: float = 0.15, stroke_size: int = 1) -> Image.Image:
    if density == 0:
        return img
    
    canvas = img.load()
    canvas_width, canvas_height = img.size
    
    if is_vertical:
        ys = _reduce_indices(range(canvas_height), density)
        for y in ys:
            grey = _random_grey()
            for x in range(origin, origin + stroke_size):
                xm = x % canvas_width
                canvas[xm, y] = grey 
                
    else:
        xs = _reduce_indices(range(canvas_width), density)
        for x in xs:
            grey = _random_grey()
            for y in range(origin, origin + stroke_size):
                ym = y % canvas_height
                canvas[x, ym] = grey
                
    return img

def backward_stripe(img: Image.Image, origin: int, /, is_vertical: bool, stroke_size: int = 1) -> Image.Image:
    canvas = img.load()
    canvas_width, canvas_height = img.size
    
    if is_vertical:
        for x in range(origin, origin + stroke_size):
            xm = x % canvas_width
            for y in range(canvas_height):
                yi = canvas_height - y - 1
                canvas[xm, y], canvas[xm, yi] = canvas[xm, yi], canvas[xm, y]
                
    else:
        for y in range(origin, origin + stroke_size):
            ym = y % canvas_height
            for x in range(canvas_width):
                xi = canvas_width - x - 1
                canvas[x, ym], canvas[xi, ym] = canvas[xi, ym], canvas[x, ym]
                
    return img

def filter_stripe(img: Image.Image, origin: int, /, is_vertical: bool, channel: channels, stroke_size: int = 1) -> Image.Image:
    canvas = img.load()
    canvas_width, canvas_height = img.size
    
    if is_vertical:
        for x in range(origin, origin + stroke_size):
            xm = x % canvas_width
            for y in range(canvas_height):
                canvas[xm, y] = _RGB_filter(canvas[xm, y], channel)
                
    else:
        for y in range(origin, origin + stroke_size):
            ym = y % canvas_height
            for x in range(canvas_width):
                canvas[x, ym] = _RGB_filter(canvas[x, ym], channel)
                
    return img

def greyscale_stripe(img: Image.Image, origin: int, /, is_vertical: bool, channel: opt_channels, stroke_size: int = 1) -> Image.Image:
    canvas = img.load()
    canvas_width, canvas_height = img.size
    
    if is_vertical:
        for x in range(origin, origin + stroke_size):
            xm = x % canvas_width
            for y in range(canvas_height):
                canvas[xm, y] = _RGB_to_greyscale(canvas[xm, y], channel)
                
    else:
        for y in range(origin, origin + stroke_size):
            ym = y % canvas_height
            for x in range(canvas_width):
                canvas[x, ym] = _RGB_to_greyscale(canvas[x, ym], channel)
                
    return img

def invert_stripe(img: Image.Image, origin: int, /, is_vertical: bool, stroke_size: int = 1) -> Image.Image:
    canvas = img.load()
    canvas_width, canvas_height = img.size
    
    if is_vertical:
        for x in range(origin, origin + stroke_size):
            xm = x % canvas_width
            for y in range(canvas_height):
                canvas[xm, y] = _invert_RGB(canvas[xm, y])
                
    else:
        for y in range(origin, origin + stroke_size):
            ym = y % canvas_height
            for x in range(canvas_width):
                canvas[x, ym] = _invert_RGB(canvas[x, ym])
                
    return img

# Blocks

def snow_block(img: Image.Image, origin: point, size: int, /, density: float = 0.15) -> Image.Image:
    if density <= 0 or size <= 0:
        return img

    canvas = img.load()

    for x, y in _produce_sparse_points(Quad.square(origin, size, img.size), density):
        canvas[x, y] = _random_grey()

    return img

def flip_block(img: Image.Image, origin: point, size: int, /, x_axis: bool, y_axis: bool) -> Image.Image:
    if not (x_axis or y_axis) or size <= 0:
        return img
    
    canvas = img.load()
    quad = Quad.square(origin, size, img.size)
    
    new_img = img.copy()
    new_canvas = new_img.load()
    
    for x, y in quad.global_points():
        xi, yi = x, y
        if x_axis:
            xi = quad.x1 + quad.x2 - x - 1
        if y_axis:
            yi = quad.y1 + quad.y2 - y - 1
        new_canvas[xi, yi] = canvas[x, y]
                
    return new_img

def filter_block(img: Image.Image, origin: point, size: int, /, channel: channels) -> Image.Image:
    canvas = img.load()
    quad = Quad.square(origin, size, img.size)
    
    for x, y in quad.global_points():
        canvas[x, y] = _RGB_filter(canvas[x, y], channel)
                
    return img

def greyscale_block(img: Image.Image, origin: point, size: int, /, channel: opt_channels = None) -> Image.Image:
    canvas = img.load()
    quad = Quad.square(origin, size, img.size)
    
    for x, y in quad.global_points():
        canvas[x, y] = _RGB_to_greyscale(canvas[x, y], channel)
                
    return img

def invert_block(img: Image.Image, origin: point, size: int, /) -> Image.Image:
    canvas = img.load()
    quad = Quad.square(origin, size, img.size)
    
    for x, y in quad.global_points():
        canvas[x, y] = _invert_RGB(canvas[x, y])
                
    return img

# All

def snow(img: Image.Image, /, density: float = 0.01) -> Image.Image:
    if density <= 0:
        return img
    
    canvas = img.load()

    for x, y in _produce_sparse_points(Quad.from_image(img), density):
        canvas[x, y] = _random_grey()

    return img

OFFSETS = ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1))

def colour_shift(img: Image.Image, /) -> Image.Image:
    directions = [rand.choice(OFFSETS) for _ in range(3)]

    canvas = img.load()
    canvas_width, canvas_height = img.size

    new_img = img.copy()
    new_canvas = new_img.load()

    for y in range(canvas_height):
        for x in range(canvas_width):
            rgb = []
            for xd, yd in directions:
                xo = (x + xd) % canvas_width
                yo = (y + yd) % canvas_height
                rgb.append(canvas[xo, yo][len(rgb)])
            new_canvas[x, y] = tuple(rgb)

    return new_img

def tear(img: Image.Image, /, max_offset: int = 16, max_sub_offset: int = 2, spacing: int = 8, count: int = 4) -> Image.Image:
    canvas = img.load()
    canvas_width, canvas_height = img.size

    new_img = img.copy()
    new_canvas = new_img.load()
    
    tear_points = frozenset(rand.sample(range(0, canvas_height, spacing), count))
    
    offset = 0
    micro_sub_offset = 0
    
    for y in range(canvas_height):
        if y in tear_points:
            offset = rand.randint(-max_offset, max_offset)
        
        if rand.random() < 0.5:
            micro_sub_offset = rand.randint(-max_sub_offset, max_sub_offset)
        
        for x in range(canvas_width):
            xo = (x + offset + micro_sub_offset) % canvas_width
            new_canvas[x, y] = canvas[xo, y]
        
    return new_img

path = '..\\Source Images\\classical-art-inspiration.png'

img = ImageOps.posterize(Image.open(path).convert('RGB'), 2)
canvas_width, canvas_height = img.size

choices = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}
block_sizes = (16, 32, 64, 128)
stripe_stroke_sizes = (2, 4, 8, 16)

# direction, position, stroke
stripe_config: list[tuple[bool, int, int]] = []

for stripe_stroke_size in stripe_stroke_sizes:
    stripe_config.extend((True, x, stripe_stroke_size) for x in range(0, canvas_width, stripe_stroke_size))
    stripe_config.extend((False, y, stripe_stroke_size) for y in range(0, canvas_height, stripe_stroke_size))

# point, size
block_config: list[tuple[point, int]] = []

for block_size in block_sizes:
    block_config.extend(((x, y), block_size) for y in range(0, canvas_height, block_size) for x in range(0, canvas_width, block_size))

rand.shuffle(stripe_config)
rand.shuffle(block_config)

iterations = min((64, len(stripe_config), len(block_config)))

for i in range(iterations):
    print(i, end=' ')
    effect = rand.choice(tuple(choices))
    
    match effect:
        case 0:
            print('snow stripe')
            choices.discard(effect)
            is_vertical, origin, stroke_size = stripe_config.pop()

            img = snow_stripe(img, origin, is_vertical, 0.16, stroke_size)
        
        case 1:
            print('backward stripe')
            choices.discard(effect)
            is_vertical, origin, stroke_size = stripe_config.pop()
            
            img = backward_stripe(img, origin, is_vertical, stroke_size)    
        
        case 2:
            print('filter stripe')
            choices.discard(effect)
            is_vertical, origin, stroke_size = stripe_config.pop()
            channel = rand.randrange(3)
            
            img = filter_stripe(img, origin, is_vertical, channel, stroke_size)
        
        case 3:
            print('greyscale stripe')
            choices.discard(effect)
            is_vertical, origin, stroke_size = stripe_config.pop()
            channel = rand.choice((None, None, None, 0, 1, 2))
            
            img = greyscale_stripe(img, origin, is_vertical, channel, stroke_size)
        
        case 4:
            print('invert stripe')
            choices.discard(effect)
            is_vertical, origin, stroke_size = stripe_config.pop()
            
            invert_stripe(img, origin, is_vertical, stroke_size)
        
        case 5:
            print('snow block')
            origin, block_size = block_config.pop()
            
            img = snow_block(img, origin, block_size, 0.15)
            
        case 6:
            print('flip block')
            origin, block_size = block_config.pop()
            x_axis, y_axis = rand.choice([(False, True), (True, False), (True, True)])
            
            img = flip_block(img, origin, block_size, x_axis, y_axis)
            
        case 7:
            print('filter block')
            origin, block_size = block_config.pop()
            channel = rand.randrange(3)
            
            img = filter_block(img, origin, block_size, channel)
            
        case 8:
            print('greyscale block')
            origin, block_size = block_config.pop()
            channel = rand.choice((None, None, None, 0, 1, 2))
            
            img = greyscale_block(img, origin, block_size, channel)
            
        case 9:
            print('invert block')
            origin, block_size = block_config.pop()
            
            img = invert_block(img, origin, block_size)

        case 10:
            print('snow')
            choices.discard(10)
            img = snow(img, 0.1)
            
        case 11:
            print('shift')
            choices.discard(11)
            img = colour_shift(img)
        
        case 12:
            print('tear')
            choices.discard(12)
            img = tear(img)
        
if 10 in choices:
    print('end snow')
    img = snow(img, 0.01)  
    
if 11 in choices:
    print('end shift')
    img = colour_shift(img)

if 12 in choices:
    print('end tear')
    img = tear(img)

print("Finished Generating")
img.show()