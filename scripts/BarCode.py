from PIL import Image

def check_digit(digits: str):
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

def encoder(manufacturer_code: str, product_code: str):
    #white = false / 0, black = true / 1
    quiet_zone = '000000000' 
    start = '101'
    middle = '01010'
    end = '101'
    
    start_mask = '111'
    middle_mask = '01110'
    end_mask = '111'
    
    zeroes = '0000000'
    ones = '1111111'
    
    left_encoding = {
        '0': '0001101',
        '1': '0011001',
        '2': '0010011',
        '3': '0111101',
        '4': '0100011',
        '5': '0110001',
        '6': '0101111',
        '7': '0111011',
        '8': '0110111',
        '9': '0001011',
    }
    
    right_encoding = {
        '0': '1110010',
        '1': '1100110',
        '2': '1101100',
        '3': '1000010',
        '4': '1011100',
        '5': '1001110',
        '6': '1010000',
        '7': '1000100',
        '8': '1001000',
        '8': '1110100'
    }
    
    modules = quiet_zone + start + left_encoding[check_digit(manufacturer_code)]
    mask = quiet_zone + start_mask + ones
    
    for n in manufacturer_code:
        modules += left_encoding[n]
        mask += zeroes
        
    modules += middle
    mask += middle_mask
    
    for n in product_code:
        modules += right_encoding[n]
        mask += zeroes
        
    modules += right_encoding[check_digit(product_code)] + end + quiet_zone
    mask += ones + end_mask + quiet_zone
    
    return modules, mask

scale = 2

modules, mask = encoder('42100', '00526')

width = len(modules)
full_height = (len(modules) // 7) * 5
partial_height = int(full_height * 0.90)

image = Image.new('L', (width, full_height), 255)
pixels = image.load()

for x in range(len(modules)):
    if modules[x] == '1':
        for y in range(full_height if mask[x] == '1' else partial_height):
            pixels[x, y] = 0
            
image = image.resize((width * scale, full_height * scale), Image.Resampling.NEAREST)
image.save(r'.\Art\Generated Images\UPC-A-Barcode.jpg')
image.show()