import win32ui
import os
from PIL import Image, ImageFilter
from random import randrange, choice
from struct import unpack
from comtypes import GUID, IUnknown, COMMETHOD, HRESULT
from ctypes.wintypes import SIZE, UINT, HBITMAP, HANDLE
from ctypes import POINTER, byref, windll, c_void_p, c_wchar_p, cast

class IShellItemImageFactory(IUnknown):
    _case_insensitive_ = True
    _iid_ = GUID('{bcc18b79-ba16-442f-80c4-8a59c30c463b}')
    _idlflags_ = []
    
IShellItemImageFactory._methods_ = [
    COMMETHOD([], HRESULT, 'GetImage',
        ( ['in'], SIZE, 'size' ),
        ( ['in'], UINT, 'flags' ),
        ( ['out'], POINTER(HBITMAP), 'phbm' )),
    ]    

LP_IShellItemImageFactory = POINTER(IShellItemImageFactory)

shell32 = windll.shell32
shell32.SHCreateItemFromParsingName.argtypes = [c_wchar_p, c_void_p, POINTER(GUID), POINTER(HANDLE)]
shell32.SHCreateItemFromParsingName.restype = HRESULT

SIIGBF_RESIZETOFIT = 0

def get_thumbnail(filename: str, icon_size: tuple[int, int]):
    """Returns thumbnail image as HBITMAP"""
    h_siif = HANDLE()
    hr = shell32.SHCreateItemFromParsingName(filename, 0,
            byref(IShellItemImageFactory._iid_), byref(h_siif))
    if hr < 0:
        raise Exception(f'SHCreateItemFromParsingName failed: {hr}')
    h_siif = cast(h_siif, LP_IShellItemImageFactory)
    # Raises exception on failure.
    return h_siif.GetImage(SIZE(*icon_size), SIIGBF_RESIZETOFIT)
    
def glitch_png_bytes(png_bytes: bytearray, iterations: int = 100) -> bytearray:
    i = 8  # skip PNG signature
    idat_ranges = []
    first_chunk = True

    # Find all IDAT chunk ranges
    while i < len(png_bytes):
        length = unpack(">I", png_bytes[i:i+4])[0]
        chunk_type = bytes(png_bytes[i+4:i+8])
        start = i + 8
        end = start + length

        if chunk_type == b'IDAT':
            # Skip first 2 bytes of first chunk (zlib header)
            s = start + 2 if first_chunk else start
            idat_ranges.append((s, end))
            first_chunk = False

        i += length + 12  # move to next chunk

    # Perform bit flips
    for _ in range(iterations):
        png_bytes[randrange(*choice(idat_ranges))] ^= 1 << randrange(0, 8)

    return png_bytes
    
def prepare_file(source_filename: str):
    root_path = os.path.dirname(__file__)
    source_pathname = os.path.join(root_path, 'Source Images', source_filename)
    file_root, extension = os.path.splitext(source_filename)
    output_pathname = os.path.join(root_path, 'Generated Images', f'glitched-{file_root}.gif')

    if extension != '.png':
        temp_pathname = os.path.join(root_path, 'Generated Images', f'TEMP-{file_root}.png')
        original_image = Image.open(source_pathname, 'r').convert('RGB')
        original_image.save(temp_pathname)
        return temp_pathname, output_pathname
    
    return source_pathname, output_pathname
    
def restore_glitched_file(temp_pathname: str, size: tuple[int, int]):
    h_bitmap = get_thumbnail(temp_pathname, size)
    pyCBitmap = win32ui.CreateBitmapFromHandle(h_bitmap)
    windll.gdi32.DeleteObject(c_void_p(h_bitmap))
    
    info = pyCBitmap.GetInfo()
    size = (info['bmWidth'], info['bmHeight'])
    
    # Get raw bitmap bytes
    data = pyCBitmap.GetBitmapBits(True)
    
    # Create PIL Image
    image = Image.frombuffer('RGBA', size, data, 'raw', 'BGRA', 0, 1)
    
    return image
    
def process_file(source_pathname: str, output_pathname: str, glitch_iterations: int, gif_iterations: int, gif_duration: float):
    """Apply glitch effect and composite with original image."""
    
    frames = []
    
    # Step 1: Open original image
    original_image = Image.open(source_pathname).convert('RGBA')
    
    # Step 2: Read and validate PNG
    with open(source_pathname, 'rb') as f:
        orignal_png_bytes = bytearray(f.read())
    if orignal_png_bytes[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError("Not a PNG")
    
    for i in range(1, gif_iterations + 1):
        # Step 3: Apply glitch to PNG bytes
        # Write of glitched file required for thumbnail algorithym to work
        glitched_png_bytes = glitch_png_bytes(orignal_png_bytes, glitch_iterations + i)
        with open(output_pathname, 'wb') as f:
            f.write(glitched_png_bytes)

        # Step 4: Restore glitched thumbnail as proper PIL Image
        glitch_image = restore_glitched_file(output_pathname, original_image.size)
        
        # Step 5: Ensure both images are same size
        glitch_image = glitch_image.resize(original_image.size)
        
        # Step 6: Create mask and composite
        mask_image = Image.new('L', original_image.size, int(255 * (0.3 + 0.4 * i / gif_iterations)))
        frame_image = Image.composite(original_image, glitch_image, mask_image).filter(ImageFilter.SHARPEN)
        frames.append(frame_image)
    
    # Step 7: Save final image
    frames[0].save(output_pathname, save_all=True, append_images=frames[1:], optimize=True, duration=(gif_duration / gif_iterations) * 1000, loop=0)

if __name__ == '__main__':
    #ref: https://stackoverflow.com/questions/67904300/how-to-get-file-thumbnail-from-windows-cache-through-python
    
    source_filename = 'voice-of-no-return.jpg'
    source_pathname, output_pathname = prepare_file(source_filename)
    glitch_iterations = 4 #8
    gif_iterations = 64 #64
    gif_duration = 15 #5
        
    process_file(source_pathname, output_pathname, glitch_iterations, gif_iterations, gif_duration)
    
    if 'TEMP' in source_pathname and os.path.exists(source_pathname):
        os.remove(source_pathname)
        
    print('Finished')