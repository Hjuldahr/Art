import json
from pathlib import Path
from typing import Iterable, NamedTuple
from PIL import Image

class ShotParams(NamedTuple):
    cam_yaw: int
    cam_pitch: int
    x_target: int 
    y_target: int 

def manual_center_crop(
    image_source: Image.Image, 
    sp: ShotParams, 
    frame_width: int,
    frame_height: int,
    x_offset: int,
    y_offset: int
) -> Image.Image:
    """Deterministic cropping engine that derives frames straight from 
    your manual targets and unified config parameters.
    """
    # Calculate the base target anchor including your macro offsets
    anchor_x = sp.x_target + x_offset
    anchor_y = sp.y_target + y_offset
    
    # Establish symmetric margins around the target anchor
    crop_x0 = anchor_x - (frame_width // 2)
    crop_x1 = crop_x0 + frame_width
    
    crop_y0 = anchor_y - (frame_height // 2)
    crop_y1 = crop_y0 + frame_height

    # Out-of-bounds safety net: fills empty edge spaces using background pixel sampling
    if crop_x0 < 0 or crop_x1 > image_source.width or crop_y0 < 0 or crop_y1 > image_source.height:
        bg_color = image_source.getpixel((5, 5))
        
        # Build an oversized temporary canvas in memory
        pad = max(frame_width, frame_height)
        padded_canvas = Image.new(
            "RGB", 
            (image_source.width + (pad * 2), image_source.height + (pad * 2)), 
            bg_color
        )
        padded_canvas.paste(image_source, (pad, pad))
        
        # Shift lookup dimensions based on the active structural pad size
        adj_x0 = crop_x0 + pad
        adj_x1 = crop_x1 + pad
        adj_y0 = crop_y0 + pad
        adj_y1 = crop_y1 + pad
        
        return padded_canvas.crop((adj_x0, adj_y0, adj_x1, adj_y1))

    return image_source.crop((crop_x0, crop_y0, crop_x1, crop_y1))

root = Path(__file__).parent
config_directory = root / 'shot_params.json'

with config_directory.open() as f:
    data = json.load(f)
    
meta, raw_shot_params = data

# Extract clean global parameters directly from the JSON metadata dictionary
in_file = root / 'sources' / meta['input_filename']
out_file_pattern = root / 'sequence frames' / meta['output_file_pattern']
out_file_pattern.parent.mkdir(exist_ok=True, parents=True)
out_file_pattern_str = str(out_file_pattern)

x_offset = meta['x_offset']
y_offset = meta['y_offset']
frame_width = meta['frame_width']
frame_height = meta['frame_height']

# Instantiate image and parameter classes
image_source = Image.open(in_file).convert('RGB')
shot_params = [ShotParams(**sp) for sp in raw_shot_params]

for i, sp in enumerate(shot_params):
    label = f'{i}_{sp.cam_yaw}_{sp.cam_pitch}'
    
    # Process the crop strictly tracking your explicit config metrics
    shot_image = manual_center_crop(
        image_source=image_source,
        sp=sp,
        frame_width=frame_width,
        frame_height=frame_height,
        x_offset=x_offset,
        y_offset=y_offset
    )
    
    shot_image.save(out_file_pattern_str.replace('%', label))