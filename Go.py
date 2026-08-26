import random
import math
from PIL import Image, ImageDraw

SIZE = 19
WIDTH = SIZE
HEIGHT = SIZE

PADDING = 0 # true stones overlap by 0.5 mm, so this is the best pixel-wise approximation
CELL_SIZE = 22 # 22.5 mm / 7.5 bu

STONE_RADIUS = CELL_SIZE // 2
HOSHI_RADIUS = round(STONE_RADIUS * 0.18) # hoshi is ~18% of the stones size

IMG_WIDTH = CELL_SIZE * WIDTH + PADDING * (WIDTH - 1)
IMG_HEIGHT = CELL_SIZE * HEIGHT + PADDING * (HEIGHT - 1)

class Colour:
    WHITE = False
    BLACK = True
    
frames: list[Image.Image] = []

def get_coordinates(grid_index):
    """Calculates the absolute pixel center for a given row or column index."""
    # Stone center is half its size, plus the accumulation of previous cells and gaps
    return (CELL_SIZE // 2) + grid_index * (CELL_SIZE + PADDING)

def render_board_frame():
    """Draws the board state cleanly using your gap-based layout."""
    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), "#DEB887")
    draw = ImageDraw.Draw(img)
    
    # Pre-calculate line locations
    line_positions = [get_coordinates(i) for i in range(SIZE)]
    
    # Draw grid lines
    for pos in line_positions:
        # Horizontal lines spanning edge to edge
        draw.line([(line_positions[0], pos), (line_positions[-1], pos)], fill="#1A1A1A", width=1)
        # Vertical lines spanning edge to edge
        draw.line([(pos, line_positions[0]), (pos, line_positions[-1])], fill="#1A1A1A", width=1)
        
    # Draw traditional star points (Hoshi) mapping correctly to indices
    star_indices = [3, 9, 15]
    for sx in star_indices:
        for sy in star_indices:
            cx = get_coordinates(sx)
            cy = get_coordinates(sy)
            #draw.ellipse([cx - r, cy - r, cx + r, cy + r])
            draw.circle([cx, cy], HOSHI_RADIUS, fill="#4A3B2C", outline="#1A1A1A", width=1)

    # Draw the stones filling their respective cells
    for y in range(HEIGHT):
        for x in range(WIDTH):
            stone = cells[y][x]
            if stone is not None:
                cx = get_coordinates(x)
                cy = get_coordinates(y)
                #bbox = [cx - stone_radius, cy - stone_radius, cx + stone_radius, cy + stone_radius]
                
                if stone == Colour.BLACK:
                    #draw.ellipse(bbox, fill="#111111", outline="#000000")
                    draw.circle([cx, cy], STONE_RADIUS, fill="#111111", outline="#000000", width=1)
                else:
                    #draw.ellipse(bbox, fill="#F5F5F5", outline="#FFFFFF")
                    draw.circle([cx, cy], STONE_RADIUS, fill="#F5F5F5", outline="#FFFFFF", width=1)
                    
    return img

cells = [[None] * WIDTH for _ in range(HEIGHT)]
occupied_cells = set()
currently_playing = Colour.BLACK

# Empty board starting point to allow Fuseki to shine
skipped = 0
max_turns = 220
turn_count = 0

frames.append(render_board_frame())

while skipped < 2 and turn_count < max_turns:
    empty_cells = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if cells[y][x] is None:
                empty_cells.append((x, y))
                
    if not empty_cells:
        break     
    
    move_weights = []
    for cx, cy in empty_cells:
        # --- 1. Opening Phase Bias (Fuseki) ---
        # Real Go players favor the 3rd and 4th lines from any edge early on
        dist_to_edge_x = min(cx, WIDTH - 1 - cx)
        dist_to_edge_y = min(cy, HEIGHT - 1 - cy)
        
        fuseki_weight = 0.05
        if turn_count < 35:
            # High reward for hitting the sweet spot lines (index 2 and 3)
            if dist_to_edge_x in (2, 3) and dist_to_edge_y in (2, 3):
                fuseki_weight += 4.5  # Corner openings
            elif dist_to_edge_x in (2, 3) or dist_to_edge_y in (2, 3):
                fuseki_weight += 2.0  # Side extensions

        # --- 2. Proximity & Density Calculation ---
        min_dist = float('inf')
        adjacent_friendly = 0
        adjacent_enemy = 0
        diagonal_friendly = 0
        
        for ox, oy in occupied_cells:
            dx = abs(cx - ox)
            dy = abs(cy - oy)
            dist = dx + dy
            
            if dist < min_dist:
                min_dist = dist
                
            # Direct orthogonal neighbors
            if dist == 1:
                if cells[oy][ox] == currently_playing:
                    adjacent_friendly += 1
                else:
                    adjacent_enemy += 1
            # Diagonal neighbors (encourages solid solidifying into blocks)
            elif dx == 1 and dy == 1:
                if cells[oy][ox] == currently_playing:
                    diagonal_friendly += 1
                    
        # Distance decay: standard attraction to active fighting zones
        combat_weight = math.exp(-0.6 * min_dist) if occupied_cells else 0.0
        
        # Boosts for localized fighting shapes
        if adjacent_enemy > 0:
            combat_weight *= 3.5
        if adjacent_friendly > 0:
            combat_weight *= 2.5
        # This diagonal bonus turns single lines into thick 2x2 solid walls
        if diagonal_friendly > 0:
            combat_weight *= 1.8
            
        # Combine opening layout drive with tactical combat weights
        final_weight = fuseki_weight + combat_weight
        move_weights.append(max(final_weight, 0.01))
        
    # 3. Select and execute move
    chosen_move = random.choices(empty_cells, weights=move_weights, k=1)[0]
    px, py = chosen_move
    
    occupied_cells.add((px, py))
    cells[py][px] = currently_playing
    
    # 4. Local crisp cleanup
    for nx, ny in [(px-1, py), (px+1, py), (px, py-1), (px, py+1)]:
        if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
            if cells[ny][nx] == (not currently_playing):
                libs = 0
                for nnx, nny in [(nx-1, ny), (nx+1, ny), (nx, ny-1), (nx, ny+1)]:
                    if 0 <= nnx < WIDTH and 0 <= nny < HEIGHT:
                        if cells[nny][nnx] is None:
                            libs += 1
                if libs == 0:
                    cells[ny][nx] = None
                    occupied_cells.discard((nx, ny))
    
    frames.append(render_board_frame())
                    
    currently_playing = not currently_playing
    turn_count += 1
    
    print(turn_count)
    
if frames:
    frames[0].save(
        "./Generated Gifs/goban_simulation.gif",
        save_all=True,
        append_images=frames[1:],
        duration=80,   # Milliseconds per frame (lower is faster)
        loop=1         # 0 means infinite loop
    )
    print(f"Successfully generated animation with {len(frames)} frames!")