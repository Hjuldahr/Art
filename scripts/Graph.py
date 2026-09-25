from __future__ import annotations
import io
from pathlib import Path
import av
import math
import random
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

# -------------------------------
# Simulation Parameters
# -------------------------------

WIDTH = 640
HEIGHT = 480
DEPTH = 100

POINT_COUNT = 400 #800

GRAPH_CONNECTIVITY = 50
GRAPH_DISCONNECTIVITY = GRAPH_CONNECTIVITY * 1.5

FPS = 10
DURATION = 30
NUM_FRAMES = FPS * DURATION

PARALLAX_FACTOR = 0.75

FORCE_SCALE = 0.0008
DAMPING = 0.97
MAX_SPEED = 1.5

BG = (0, 0, 0)

# -------------------------------
# Utilities
# -------------------------------

def pil_gif_to_mp4_bytes(frames):
    # Prepare buffer and container
    buf = io.BytesIO()
    container = av.open(buf, mode="w", format="mp4")
    
    # Setup stream (h264)
    stream = container.add_stream("libx264", rate=FPS) # Adjust FPS as needed
    stream.width = frames[0].width
    stream.height = frames[1].height
    stream.pix_fmt = "yuv420p"

    # Iterate through GIF frames
    for frame in frames:
        # Convert PIL to numpy array
        img_array = np.array(frame.convert("RGB"))
        av_frame = av.VideoFrame.from_ndarray(img_array, format="rgb24")
        
        # Encode frame
        for packet in stream.encode(av_frame):
            container.mux(packet)

    # Flush encoder
    for packet in stream.encode():
        container.mux(packet)
    
    container.close()
    buf.seek(0)
    return buf

def toroidal_delta(d, size):
    if d > size / 2:
        d -= size
    elif d < -size / 2:
        d += size
    return d

def toroidal_distance(p1, p2):
    dx = abs(p2.x - p1.x)
    dy = abs(p2.y - p1.y)
    dz = abs(p2.z - p1.z)

    dx = min(dx, WIDTH - dx)
    dy = min(dy, HEIGHT - dy)
    dz = min(dz, DEPTH - dz)

    return math.sqrt(dx*dx + dy*dy + dz*dz)

def distance(p1, p2):
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    dz = p2.z - p1.z
    return math.sqrt(dx*dx + dy*dy + dz*dz)

def project(p):
    scale = PARALLAX_FACTOR + (p.z / DEPTH)
    screen_x = (p.x - WIDTH/2) * scale + WIDTH/2
    screen_y = (p.y - HEIGHT/2) * scale + HEIGHT/2
    return screen_x, screen_y

# -------------------------------
# Point Class
# -------------------------------

class Point:
    def __init__(self, i, x, y, z):
        self.i = i
        self.x = x
        self.y = y
        self.z = z

        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0

        self.connections = set()

    def __hash__(self):
        return hash(self.i)

# -------------------------------
# Physics Step
# -------------------------------

def apply_forces(points, repel=10000, attract=0.001):
    forces = {p.i: [0.0, 0.0, 0.0] for p in points}

    for i, p1 in enumerate(points):
        for p2 in points[i+1:]:

            dx = toroidal_delta(p2.x - p1.x, WIDTH)
            dy = toroidal_delta(p2.y - p1.y, HEIGHT)
            dz = toroidal_delta(p2.z - p1.z, DEPTH)

            dist_sq = dx*dx + dy*dy + dz*dz

            if dist_sq < 0.0001:
                continue

            dist = math.sqrt(dist_sq)
            #f = FORCE_STRENGTH / (dist_sq + 0.01)
            f = (repel / (dist_sq + 0.0001)) - (attract * dist)

            fx = f * dx / dist
            fy = f * dy / dist
            fz = f * dz / dist

            forces[p1.i][0] -= fx
            forces[p1.i][1] -= fy
            forces[p1.i][2] -= fz

            forces[p2.i][0] += fx
            forces[p2.i][1] += fy
            forces[p2.i][2] += fz

    # Integrate with damping
    for p in points:

        ax, ay, az = forces[p.i]

        p.vx += ax * FORCE_SCALE
        p.vy += ay * FORCE_SCALE
        p.vz += az * FORCE_SCALE

        p.vx *= DAMPING
        p.vy *= DAMPING
        p.vz *= DAMPING

        speed = math.sqrt(p.vx**2 + p.vy**2 + p.vz**2)
        if speed > MAX_SPEED:
            scale = MAX_SPEED / speed
            p.vx *= scale
            p.vy *= scale
            p.vz *= scale

        p.x = (p.x + p.vx) % WIDTH
        p.y = (p.y + p.vy) % HEIGHT
        p.z = (p.z + p.vz) % DEPTH

# -------------------------------
# Simulation Setup
# -------------------------------

points = [
    Point(i,
          random.uniform(0, WIDTH),
          random.uniform(0, HEIGHT),
          random.uniform(0, DEPTH))
    for i in range(POINT_COUNT)
]

frames = []

# -------------------------------
# Main Loop
# -------------------------------

for t in range(NUM_FRAMES):
    print(f"Frame {t}/{NUM_FRAMES}")

    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    apply_forces(points)

    points.sort(key=lambda p: p.z)

    for i, p1 in enumerate(points):
        for p2 in points[i+1:]:

            #dist = toroidal_distance(p1, p2)
            dist = distance(p1, p2)

            red_mode = True

            if dist < GRAPH_CONNECTIVITY:
                p1.connections.add(p2)
                p2.connections.add(p1)
                red_mode = False

            elif dist > GRAPH_DISCONNECTIVITY:
                p1.connections.discard(p2)
                p2.connections.discard(p1)
                continue

            elif p2 not in p1.connections:
                continue

            colour = int(((p1.z + p2.z) / 2) / DEPTH * 255)

            x1, y1 = project(p1)
            x2, y2 = project(p2)

            fill = (colour, 0, 0) if red_mode else (colour, colour, colour)
            draw.line([(x1, y1), (x2, y2)], fill=fill, width=1)

    # Draw nodes
    for p in points:
        colour = int((p.z / DEPTH) * 255)
        x, y = project(p)
        draw.point((x, y), fill=(colour, colour, colour))

    # Glow pass
    image = image.filter(ImageFilter.GaussianBlur(0.5))
    
    frames.append(image)

# -------------------------------
# Save GIF
# -------------------------------

print('Writing MP4')
mp4_buffer = pil_gif_to_mp4_bytes(frames)
Path("./Generated Gifs/graph.mp4").write_bytes(mp4_buffer.getvalue())