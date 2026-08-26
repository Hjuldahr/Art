import math
from typing import Any
from PIL import Image, ImageFilter, ImageChops 
import colorsys
from collections.abc import Mapping, Iterable

TAU = 2 * math.pi

class FuzzyDict:
    def __init__(self, entries: dict | Iterable[tuple]):
        if isinstance(entries, (Mapping, Iterable)):
            self.entries = dict(entries)
        else:
            raise TypeError('Entries must be a dict or an iterable of tuples')
        
        self._sorted_keys = sorted(self.entries.keys())

    def find_closest(self, search_term):
        # Iterates over large entry pools faster than linear search
        keys = self._sorted_keys
        if not keys: return None
        
        low = 0
        high = len(keys) - 1
        
        while high - low > 1:
            mid = (low + high) // 2
            if search_term < keys[mid]:
                high = mid  # Trim right half
            elif search_term > keys[mid]:
                low = mid   # Trim left half
            else:
                return self.entries[keys[mid]] # Exact match

        if abs(keys[low] - search_term) <= abs(keys[high] - search_term):
            return self.entries[keys[low]]
        return self.entries[keys[high]]
        
    def __getitem__(self, key: int | float) -> Any:
        return self.find_closest(key)
    
    def get(self, key: int | float, fallback: Any) -> Any:
        return self.find_closest(key) or fallback
    
    def __setitem__(self, key: int | float, value: Any):
        self.entries[key] = value
        self._sorted_keys = sorted(self.entries.keys())
        
    def setdefault(self, key: int | float, optional: Any) -> Any:
        if optional not in self.entries:
            self.entries[key] = optional
            self._sorted_keys = sorted(self.entries.keys())
            return optional
        else:
            return self.entries[key]
        
    def __str__(self) -> str:
        return f'{{{",".join(f"{k}:{self.entries[k]}" for k in self._sorted_keys)}}}'
    
CHAR_WIDTH = 8
CHAR_HEIGHT = 15
CHAR_SIZE = (CHAR_WIDTH, CHAR_HEIGHT)
VERTICAL_CHAR_PADDING = 1
HORIZONTAL_CHAR_PADDING = 1
CHAR_PADDING = (HORIZONTAL_CHAR_PADDING, VERTICAL_CHAR_PADDING)    
    
BG = (0,0,0)    
    
GREYSCALE_MAP = FuzzyDict({
    0.0000: ' ', 
    0.0751: '`', 
    0.0829: '.', 
    0.0848: '-', 
    0.1227: "'", 
    0.1403: ':', 
    0.1559: '_', 
    0.1850: ',', 
    0.2183: '^', 
    0.2417: '=', 
    0.2571: ';', 
    0.2852: '>', 
    0.2902: '<', 
    0.2919: '+', 
    0.3099: '!', 
    0.3192: 'r', 
    0.3232: 'c', 
    0.3294: '*', 
    0.3384: '/', 
    0.3609: 'z', 
    0.3619: '?', 
    0.3667: 's', 
    0.3737: 'L', 
    0.3747: 'T', 
    0.3838: 'v', 
    0.3921: ')', 
    0.3960: 'J', 
    0.3984: '7', 
    0.3993: '(', 
    0.4075: '|', 
    0.4091: 'F', 
    0.4101: 'i', 
    0.4200: '{', 
    0.4230: 'C', 
    0.4247: '}', 
    0.4274: 'f', 
    0.4293: 'I', 
    0.4328: '3', 
    0.4382: '1', 
    0.4385: 't', 
    0.4420: 'l', 
    0.4473: 'u', 
    0.4477: '[', 
    0.4503: 'n', 
    0.4562: 'e', 
    0.4580: 'o', 
    0.4610: 'Z', 
    0.4638: '5', 
    0.4667: 'Y', 
    0.4686: 'x', 
    0.4693: 'j', 
    0.4703: 'y', 
    0.4833: 'a', 
    0.4881: ']', 
    0.4944: '2', 
    0.4953: 'E', 
    0.4992: 'S', 
    0.5509: 'w', 
    0.5567: 'q', 
    0.5569: 'k', 
    0.5591: 'P', 
    0.5602: 'h', 
    0.5650: '9', 
    0.5776: 'd', 
    0.5777: '4', 
    0.5818: 'V', 
    0.5870: 'p', 
    0.5972: 'O', 
    0.5999: 'G', 
    0.6043: 'b', 
    0.6049: 'U', 
    0.6093: 'A', 
    0.6099: 'K', 
    0.6465: 'X', 
    0.6561: 'H', 
    0.6595: 'm', 
    0.6631: '8', 
    0.6714: 'R', 
    0.6759: 'D', 
    0.6809: '#', 
    0.6816: '$', 
    0.6925: 'B', 
    0.7039: 'g', 
    0.7086: '0', 
    0.7235: 'M', 
    0.7302: 'N', 
    0.7332: 'W', 
    0.7602: 'Q', 
    0.7834: '%', 
    0.8037: '&', 
    0.9999: '@'
})

EDGE_MAP = FuzzyDict({
    0:           '⎹',
    math.pi/4:   '╲',
    math.pi/2:   '‾',
    3*math.pi/4: '╱',
    math.pi:     '⎸',
    5*math.pi/4: '╲',
    3*math.pi/2: '_',
    7*math.pi/4: '╱'
})

MAX_MAG = 4 * math.sqrt(2) 

SOBEL_CUTOFF = 0.33
KERNEL_SIZE = 3
X_KERNEL = ((-1, 0, 1),
            (-2, 0, 2),
            (-1, 0, 1))
Y_KERNEL = ((-1,-2,-1),
            ( 0, 0, 0),
            ( 1, 2, 1))

def sobel_filter(image: Image.Image):
    image = image.convert('L')
    pixels = image.load()
    WIDTH, HEIGHT = image.size
    
    sobel_image = Image.new('RGB', image.size, BG)
    sobel_pixels = sobel_image.load()
    
    # Skip outermost pixels the filter may enclose the image in a box
    for img_y in range(1, HEIGHT-1):
        for img_x in range(1, WIDTH-1):
            # Set Accumalators
            x_accumulator, y_accumulator = 0, 0
            
            # Apply Convulation
            for k_y in range(KERNEL_SIZE):
                px_y = k_y + img_y - 1
                
                for k_x in range(KERNEL_SIZE):
                    px_x = k_x + img_x - 1

                    px = (pixels[px_x, px_y] - 128) / 255
                    x_accumulator += X_KERNEL[k_y][k_x] * px
                    y_accumulator += Y_KERNEL[k_y][k_x] * px
                        
            magnitude = math.sqrt(x_accumulator ** 2 + y_accumulator ** 2)            
            theta = math.atan2(y_accumulator, x_accumulator)
            
            if magnitude < SOBEL_CUTOFF:
                continue
            
            hue = (theta + math.pi) / TAU
            #val = min(1.0, mag / MAX_MAG)
            
            rgb = tuple(
                int(255 * c) for c 
                in colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            )     
            sobel_pixels[img_x, img_y] = rgb
            
    return sobel_image

def ASCII_filter(image: Image.Image):
    image = image.convert('L')
    pixels = image.load()
    WIDTH, HEIGHT = image.size
    
    text = ''
    
    for img_y in range(0, HEIGHT, CHAR_HEIGHT + VERTICAL_CHAR_PADDING):
        for img_x in range(0, WIDTH, CHAR_WIDTH + HORIZONTAL_CHAR_PADDING):
            
            accumulator = 0
            
            for char_y in range(0, CHAR_HEIGHT):
                px_y = min(char_y + img_y, HEIGHT-1)
                
                for char_x in range(0, CHAR_WIDTH):
                    px_x = min(char_x + img_x, WIDTH-1)
                    
                    px = pixels[px_x, px_y] / 255
                    accumulator += px
                    
            brightness = accumulator / (CHAR_WIDTH * CHAR_HEIGHT)
            
            text += GREYSCALE_MAP[brightness]
            
        text += '\n'
        
    return text

def gaussian_blur(image: Image.Image, strength=1.0):
    kernel = [0.25, 0.5, 0.25]
    radius = 1
    
    pixels = image.load()
    WIDTH, HEIGHT = image.size
    
    temp_image = Image.new('RGB', image.size, (0,0,0))
    temp_pixels = temp_image.load()  
    
    for y in range(HEIGHT):
        for x in range(1, WIDTH-1):
            accumalator = [0,0,0]
            for offset in range(3):
                px = pixels[x+offset-1, y]
                for k in range(3):
                    accumalator[k] += px[k] * kernel[offset]
            temp_pixels[x,y] = int(accumalator)      
            
    for y in range(HEIGHT):
        for x in range(1, WIDTH-1):
            summation = (temp_pixels[x-1, y] * kernel[0]) + (temp_pixels[x, y] * kernel[1]) + (temp_pixels[x+1, y] * kernel[2])
            pixels[x,y] = int(summation)
            
    image.show()

def difference_of_gaussians(image: Image.Image, factor=1.0):
    fine_grained = image.filter(ImageFilter.GaussianBlur(factor))
    coarse_grained = image.filter(ImageFilter.GaussianBlur(factor * 1.6))
    difference = ImageChops.subtract(fine_grained, coarse_grained, offset=128)
    difference.show('difference_of_gaussians')

def ASCII_sobel_filter(image: Image.Image):
    image = image
    pixels = image.load()
    WIDTH, HEIGHT = image.size
    
    text = ''
    for img_y in range(0, HEIGHT, CHAR_HEIGHT + VERTICAL_CHAR_PADDING):
        for img_x in range(0, WIDTH, CHAR_WIDTH + HORIZONTAL_CHAR_PADDING):
            hue_accumulator = 0
            val_accumulator = 0
            
            for char_y in range(0, CHAR_HEIGHT):
                px_y = min(char_y + img_y, HEIGHT-1)
                
                for char_x in range(0, CHAR_WIDTH):
                    px_x = min(char_x + img_x, WIDTH-1)
                    
                    px = pixels[px_x, px_y]
                    hsv = colorsys.rgb_to_hsv(px[0] / 255, px[1] / 255, px[2] / 255)
                    hue_accumulator += hsv[0]
                    val_accumulator  += hsv[2]
                        
            hue = hue_accumulator / (CHAR_WIDTH * CHAR_HEIGHT)
            val = val_accumulator / (CHAR_WIDTH * CHAR_HEIGHT)
            
            if val >= SOBEL_CUTOFF:
                text += EDGE_MAP[hue]
            else:
                text += ' '
        text += '\n'
        
    return text

if __name__ == '__main__':
    image = Image.open('Source Images\\360_F_369634160_Pv5jIedHbMhEoCeaL4GwXYky3Ij0QY1f.jpg')
    
    gaussian_blur(image)
    
    #difference_of_gaussians(image)
    
    #greyscale_image = Image.open('Source Images\\circle.jpg').convert('L')
    #sobel_image = sobel_filter(greyscale_image)
    #sobel_image.save('Generated Images\\SOBEL_circle.jpg')
    
    """
    ascii_sobel_text = ASCII_sobel_filter(sobel_image)

    ascii_text = ASCII_filter(greyscale_image)
    
    combined_ascii_text = ''
    for sobel_line, line in zip(ascii_sobel_text.splitlines(), ascii_text.splitlines()):
        for sobel_char, char in zip(sobel_line, line):
            if sobel_char == ' ':
                combined_ascii_text += char
            else:
                combined_ascii_text += sobel_char
        combined_ascii_text += '\n'
        
    with open('Generated Images\\SOBEL_circle.text', 'w', encoding='utf-8') as f:
        f.write(combined_ascii_text)
    """