from PIL import Image

def bin_to_dec(bits):
    return int("".join("1" if b else "0" for b in bits), 2)

def decode_payload(grid):
    size = len(grid)

    # parity guess
    # try both possibilities
    for isEven in (True, False):

        v = [[False]*size for _ in range(size)]

        for y in range(size):
            for x in range(size):
                mask = (x * y) % 2 == 0
                v[y][x] = grid[y][x] ^ mask ^ isEven

        x_bits = [False]*size
        y_bits = [False]*size

        x_bits[0] = True

        for y in range(size):
            y_bits[y] = v[y][0] ^ x_bits[0]

        for x in range(size):
            x_bits[x] = v[0][x] ^ y_bits[0]

        if x_bits[0] and y_bits[0]:
            return x_bits[1:], y_bits[1:]

    raise ValueError("Failed to decode")

def decode_image(img):
    #img = Image.open(path).convert("L")
    pixels = img.load()

    # find payload bounds manually
    # (assumes same margin/spacing as encoder)

    margin = 4
    spacing = 1
    displace = margin + spacing*2 + 1

    width = 21
    height = 21

    grid = []

    for y in range(height):
        row = []
        for x in range(width):
            px = pixels[margin + spacing + x + 1,
                        margin + spacing + y + 1]
            row.append(px == 0)
        grid.append(row)

    x_bits, y_bits = decode_payload(grid)

    x_val = bin_to_dec(x_bits)
    y_val = bin_to_dec(y_bits)

    x_str = str(x_val).zfill(6)
    y_str = str(y_val).zfill(6)

    manufacturer_checksum = x_str[0]
    manufacturer_code = x_str[1:]

    product_code = y_str[:5]
    product_checksum = y_str[5]

    return manufacturer_code, product_code

#################################################

def checksum(digits: str):
    # step 1
    checksum = sum(int(n) for n in digits[1::2])
    # step 2
    checksum *= 3
    # step 3
    checksum += sum(int(n) for n in digits[0::2])
    # step 4
    checksum %= 10
    # step 5
    return '0' if checksum == 0 else str(10 - checksum)   

def dec_to_bin(num: int, padding) -> list[bool]:
    bit_str = bin(int(num)).removeprefix('0b').zfill(padding)
    return [bit == '1' for bit in bit_str]

def encode(x_module: list[bool], y_module: list[bool]):
    width = len(x_module)
    height = len(y_module)
    count = sum(x_module) + sum(y_module)
    isEven = count % 2 == 0
    offset = 0 if isEven else 1 # Black=Even / White=Odd

    grid = []
    for y, y_bit in enumerate(y_module):
        row = []
        for x, x_bit in enumerate(x_module):
            mask = (x * y) % 2 == 0
            bit = ((x_bit ^ y_bit) ^ mask) ^ isEven
            row.append(bit)
        grid.append(row)
    
    scale = 2 # export size
    margin = 4 # THICKNESS of whitespace
    spacing = 1 # GAP between payload and border
    image_size = (width + (spacing * 2) + (margin * 2) + 2, height + (spacing * 2) + (margin * 2) + 2)
    image = Image.new('L', image_size, 255)
    pixels = image.load()
    
    displace = margin + (spacing * 2) + 1
    
    # Payload
    for y in range(height):
        for x in range(width):
            if grid[y][x]:
                pixels[margin + spacing + x + 1, margin + spacing + y + 1] = 0
    
    # Row Picket Fence
    for y in range(margin + offset, height + displace, 2):
        pixels[margin, y] = 0
            
    # Column Picket Fence
    for x in range(margin + offset, width + displace, 2):  
        pixels[x, margin] = 0  
        
    # Row Terminator
    x = width + displace
    for y in range(margin, height + displace + 1):
        pixels[x, y] = 0
        
    # Column Terminator
    y = height + displace
    for x in range(margin, width + displace + 1):
        pixels[x, y] = 0
        
    image = image.resize((image_size[0] * scale, image_size[1] * scale), Image.Resampling.NEAREST)
        
    return image

manufacturer_code = '42100'
product_code = '00526'

manufacturer_checksum = checksum(manufacturer_code)
product_checksum = checksum(product_code)

x_module = dec_to_bin(manufacturer_checksum + manufacturer_code, 20)
y_module = dec_to_bin(product_code + product_checksum, 20)

x_module.insert(0, True)
y_module.insert(0, True)

image = encode(x_module, y_module)

image.save('./Generated Images/UPC-A-Barsquare.jpg')
image.show()

#############################

# Not working
print(decode_image(image))