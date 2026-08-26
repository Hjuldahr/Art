import hashlib
import math
import os
from PIL import Image

class BinaryVisualizer():
    def __init__(self):
        pass
    
    def _1d_to_2d(self, i, side):
        return i % side, i // side
    
    def _get_image(self, side):
        image = Image.new('RGB', (side, side), (0,0,0))
        return image, image.load()
    
    def _get_side(self, area):
        return math.ceil(math.sqrt(area))
    
    def _save_image(self, image, file_path, suffix):
        #name = file_path.split('\\')[-1].split('.')[0]
        output_path = os.path.join(os.path.dirname(__file__), 'Generated Images')
        os.makedirs(output_path, exist_ok=True)
        file_name = os.path.basename(file_path).split('.', 1)[0] + f'_{suffix}.png'
        output_path = os.path.join(output_path, file_name)
        image.save(output_path)
    
    def bit_level(self, file_path):
        bit_blocks = []
        with open(file_path, mode='rb') as f:
            byte = f.read(1)  
            while byte:  
                #byte = byte[0] #convert from bytes to int
                bit_blocks.extend([(byte >> i) & 1 == 1 for i in range(7, -1, -1)])
                byte = f.read(1)  
                    
                if len(bit_blocks) % 8e+6 == 0:
                    print (len(bit_blocks) // 8e+6)

        bit_block_count = len(bit_blocks)
        side = self._get_side(bit_block_count)
        image, pixels = self._get_image(side)
        
        for i in range(bit_block_count):
            x, y = self._1d_to_2d(i, side)
            v = 255 if bit_blocks[i] else 0
            pixels[x, y] = (v, v, v)   
            
        self._save_image(image, file_path, 'bits')

    def byte_level(self, file_path):
        byte_blocks = []
        with open(file_path, mode='rb') as f:
            byte = f.read(1)   
            while byte:       
                byte_blocks.append(byte)
                byte = f.read(1)   
                
                if len(byte_blocks) % 1e+6 == 0:
                    print (len(byte_blocks) // 1e+6)
            
        byte_block_count = len(byte_blocks)
        side = self._get_side(byte_block_count) 
        image, pixels = self._get_image(side)
        
        for i in range(byte_block_count):
            x, y = self._1d_to_2d(i, side)
            v = byte_blocks[i][0]
            pixels[x,y] = (v,v,v)
            
        self._save_image(image, file_path, 'bytes')
        
    def _pad_bytes(self, byte_block, size):
        return byte_block + b'\x00' * (3 - len(byte_block))
                
    def triplet_level(self, file_path):
        byte_blocks = []
        
        with open(file_path, mode='rb') as f:
            triplet = f.read(3)  
            while triplet:
                triplet = self._pad_bytes(triplet, 3)
                byte_blocks.append(tuple(triplet))
                triplet = f.read(3)  
                
                if len(byte_blocks) % 333333 == 0:
                    print (len(byte_blocks) // 333333)

        byte_block_count = len(byte_blocks)
        side = self._get_side(byte_block_count)
        image, pixels = self._get_image(side)
        
        for i in range(byte_block_count):
            x, y = self._1d_to_2d(i, side)
            pixels[x,y] = byte_blocks[i]
            
        self._save_image(image, file_path, 'triplets')

if __name__ == '__main__':
    file_path = 'c:\\Windows\\System32\\MRT.exe' #c:\\Program Files\\PuTTY\\putty.exe
    bv = BinaryVisualizer()
    
    print("triplets")
    bv.triplet_level(file_path)
    
    #print("bytes")
    #bv.byte_level(file_path)
    
    #print("bits")
    #bv.bit_level(file_path)

    print("done")