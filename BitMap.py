from pathlib import Path
import random
from PIL import Image, ImageSequence

ROOT_PATH = Path(__file__).resolve().parent
IN_FILE = 'sample_2.gif'
IN_PATH = ROOT_PATH / 'Source Images' / IN_FILE
OUT_PATH = ROOT_PATH / 'Generated Images' / f'bcrupted_{IN_FILE}'

THRESHOLDS = {'R': 128, 'G': 25, 'B': 25, 'K': 200}
MASKS = {c: 0 if random.randint(0, 255) < i else 255 for i in range(256) for c in ('R','G','B','K')}

def rgb_to_grey(r: int, g: int, b: int) -> int:
    return min(max(int(0.3 * r + 0.6 * g + 0.11 * b), 0), 255)

def normalize(c: str, v: int) -> int:
    return 0 if v < THRESHOLDS[c] or MASKS[c] > v else 255

gif = Image.open(IN_PATH, mode='r')
frame_durations = []
new_frames = []

for frame in ImageSequence.Iterator(gif):
    frame = frame.convert('RGB')
    frame_pixels = frame.load()
    
    new_frame = Image.new('1', frame.size, 0)
    new_frame_pixels = new_frame.load()
    
    for y in range(frame.height):
        for x in range(frame.width):
            r, g, b = frame_pixels[x, y]

            r = normalize('R', r)
            g = normalize('G', g)
            b = normalize('B', b)
            
            k = rgb_to_grey(r, g, b)
            k = normalize('K', k)
            
            new_frame_pixels[x, y] = k

    frame_durations.append(frame.info['duration'])
    new_frames.append(new_frame)

new_frames[0].save(
    OUT_PATH,
    save_all=True,
    append_images=new_frames[1:],
    duration=frame_durations, # ms per frame
    loop=0
)
print("Done!")