from __future__ import annotations
from PIL import Image, ImageSequence, ImageFilter
import av
import numpy as np

def gif_to_mp4(
    output_path: str, 
    frames: np.ndarray, # Matching the shape (N, H, W, 3) and dtype uint8
    durations: np.ndarray, 
    crf: int = 23, 
    preset: str = "medium"
):
    if frames.size == 0:
        raise ValueError("GIF contains no frames.")

    # Calculate approximate FPS from average duration
    # durations is np.uint16 per your signature
    avg_duration_ms = np.mean(durations)
    fps = max(1, round(1000 / avg_duration_ms))

    # H.264 requires even dimensions. 
    # Shape is (N, Height, Width, Channels)
    orig_height, orig_width = frames.shape[1], frames.shape[2]
    width = orig_width // 2 * 2
    height = orig_height // 2 * 2

    # Open output container
    container = av.open(output_path, mode="w", format="mp4")

    stream = container.add_stream("libx264", rate=fps)
    stream.width = width
    stream.height = height
    stream.pix_fmt = "yuv420p"
    stream.options = {
        "crf": str(crf),
        "preset": preset,
    }

    for i in range(frames.shape[0]):
        # Slice the 4D array to get a 3D frame (H, W, 3)
        frame_array = frames[i]

        # Handle resizing if dimensions were odd and had to be truncated
        if orig_width != width or orig_height != height:
            # We crop/slice to the even dimensions for H.264 compatibility
            frame_array = frame_array[:height, :width, :]

        video_frame = av.VideoFrame.from_ndarray(frame_array, format="rgb24")

        for packet in stream.encode(video_frame):
            container.mux(packet)

    # Flush encoder
    for packet in stream.encode():
        container.mux(packet)

    container.close()

TRAIL_LIFESPAN = 60 
COLOURS = []

for i in range(TRAIL_LIFESPAN):
    # Progress from 0.0 (start of trail) to 1.0 (end of trail)
    rel_pos = i / TRAIL_LIFESPAN 
    
    if rel_pos < 0.5:
        # PHASE 1: Blue to Red transition (The "Shift")
        # Maps 0.0-0.5 to a 0.0-1.0 transition ratio
        ratio = rel_pos * 2
        r = int(255 * ratio)       # Red increases
        b = int(255 * (1 - ratio)) # Blue decreases
    else:
        # PHASE 2: Red to Black transition (The "Fade")
        # Maps 0.5-1.0 to a 0.0-1.0 transition ratio
        ratio = (rel_pos - 0.5) * 2
        r = int(255 * (1 - ratio)) # Red fades out
        b = 0                      # Blue is already gone
        
    COLOURS.append((r, 0, b))   
    
COLOURS = np.array(COLOURS[::-1], dtype=np.uint8)

gif = Image.open("./Source Images/apple.gif")

EDGE_COLOUR = Image.new("RGB", gif.size, (255, 255, 255)) 

frames = np.zeros((gif.n_frames, gif.height, gif.width, 3), dtype=np.uint8)
durations = np.zeros(gif.n_frames, dtype=np.uint16)
history = np.zeros((gif.height, gif.width), dtype=np.uint8)

print (f'Processing {gif.n_frames} frames')

# start of history
gif.seek(0)

edges = gif.convert('L').filter(ImageFilter.FIND_EDGES).point(lambda x: 255 if x > 20 else 0)
frames[0] = np.array(edges.convert('RGB'))
durations[0] = gif.info.get("duration", 50)

prev_frame = gif.convert('RGB')

for i in range(1, gif.n_frames):
    gif.seek(i)
    curr_frame = gif.convert("RGB")
    
    # 1. Convert frames to NumPy arrays
    curr_np = np.array(curr_frame)
    prev_np = np.array(prev_frame)

    # 2. Update history: Set to TRAIL_LIFESPAN where pixels changed
    # (curr_np != prev_np).any(axis=2) finds where R, G, or B differs
    changed_mask = (curr_np != prev_np).any(axis=2)
    history[changed_mask] = TRAIL_LIFESPAN

    # 3. Create the trail canvas
    # Create an empty black image array
    canvas_np = np.zeros((gif.height, gif.width, 3), dtype=np.uint8)
    
    # Where history > 0, map the history value to the COLOURS array
    active_mask = history > 0
    indices = history[active_mask] - 1
    canvas_np[active_mask] = COLOURS[indices]

    # 4. Decay history for the next frame
    history[active_mask] -= 1

    # 5. Convert back to Pillow to handle the Edge Filter
    canvas = Image.fromarray(canvas_np)
    edges = curr_frame.convert('L').filter(ImageFilter.FIND_EDGES).point(lambda x: 255 if x > 20 else 0)
    
    # 6. Composite
    frame_with_edges = Image.composite(EDGE_COLOUR, canvas, edges)
    
    frames[i] = np.array(frame_with_edges)
    durations[i] = curr_frame.info.get("duration", 50)
    
    prev_frame = curr_frame.copy()

print (f'Encoding to MP4')
gif_to_mp4("./Generated Gifs/chromatic_apple.mp4", frames, durations)
print('Done')