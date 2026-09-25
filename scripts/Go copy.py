from collections import deque
from dataclasses import dataclass
import random
import math
from PIL import Image, ImageDraw

SIZE = 19
WIDTH = SIZE
HEIGHT = SIZE

PADDING = 0 # true stones overlap by 0.5 mm, so this is the best pixel-wise approximation
CELL_SIZE = 22 # 22.5 mm / 7.5 bu

BOARD_BORDER = 11

STONE_RADIUS = CELL_SIZE // 2
HOSHI_RADIUS = round(STONE_RADIUS * 0.18) # hoshi is ~18% of the stones size

IMG_WIDTH = CELL_SIZE * WIDTH + PADDING * (WIDTH - 1)
IMG_HEIGHT = CELL_SIZE * HEIGHT + PADDING * (HEIGHT - 1)

INNER_BOARD = [ BOARD_BORDER, BOARD_BORDER, IMG_WIDTH - BOARD_BORDER, IMG_HEIGHT - BOARD_BORDER ]

SHENG_PHASE_LENGTH = 5
KE_PHASE_LENGTH = 5
WUXING_PHASE_LENGTH = SHENG_PHASE_LENGTH + KE_PHASE_LENGTH

@dataclass(frozen=True)
class Colour:
    ordinal: int
    fill: str
    outline: str

class StoneColours:
    WOOD = Colour(0, '#8CB6A6', '#80B0A0')
    FIRE = Colour(1, '#CD071E', '#C00010')
    EARTH = Colour(2, '#FFB200', '#F0F000')
    METAL = Colour(3, '#E2E5DE', '#E0E0D0')
    WATER = Colour(4, '#161718', '#101010')
    
    GENERATES = {
        WOOD: FIRE,
        FIRE: EARTH,
        EARTH: METAL,
        METAL: WATER,
        WATER: WOOD
    }
    CONTROLS = {
        WOOD: EARTH,
        EARTH: WATER,
        WATER: FIRE,
        FIRE: METAL,
        METAL: WOOD 
    }
    
    ORDINALS = (WOOD, FIRE, EARTH, METAL, WATER, WOOD, EARTH, WATER, FIRE, METAL) # Generative -> Destructive Cycle chaining experiment
    SIZE = 10
    
class BoardColours:
    SHENG_BOARD = Colour(0, '#DEB887', '#BE9867')
    KE_BOARD = Colour(1, '#87ADDE', '#658CBD')
    INK = Colour(2, '#1A1A1A', '#1A1A1A')
    SHENG_HOSHI = Colour(3, '#4A3B2C', '#1A1A1A')
    KE_HOSHI = Colour(4, '#2C3B49', '#1A1A1A')
    
    PHASE = ((SHENG_BOARD, SHENG_HOSHI), (KE_BOARD, KE_HOSHI))
    
def get_wuxing_phase(turn_count):
    return (turn_count % WUXING_PHASE_LENGTH) // SHENG_PHASE_LENGTH
    
def get_coordinates(grid_index):
    """Calculates the absolute pixel center for a given row or column index."""
    # Stone center is half its size, plus the accumulation of previous stones and gaps
    return STONE_RADIUS + grid_index * (CELL_SIZE + PADDING)

def render_board_frame(turn_count, stones):
    """Draws the board state using the current Sheng/Ke phase."""
    phase_index = get_wuxing_phase(turn_count)
    board_colour, hoshi_colour = BoardColours.PHASE[phase_index]

    img = Image.new(
        "RGB",
        (IMG_WIDTH, IMG_HEIGHT),
        board_colour.outline
    )

    draw = ImageDraw.Draw(img)

    line_positions = [
        get_coordinates(i)
        for i in range(SIZE)
    ]

    # Inner board surface, leaving the outline as a border
    draw.rectangle(
        INNER_BOARD,
        fill=board_colour.fill
    )

    # Draw grid lines
    for pos in line_positions:
        draw.line(
            [
                (line_positions[0], pos),
                (line_positions[-1], pos)
            ],
            fill=BoardColours.INK.fill,
            width=1
        )
        draw.line(
            [
                (pos, line_positions[0]),
                (pos, line_positions[-1])
            ],
            fill=BoardColours.INK.fill,
            width=1
        )

    # Hoshi
    star_indices = [3, 9, 15]

    for sx in star_indices:
        for sy in star_indices:
            cx = get_coordinates(sx)
            cy = get_coordinates(sy)

            draw.circle(
                [cx, cy],
                HOSHI_RADIUS,
                fill=hoshi_colour.fill,
                outline=hoshi_colour.outline,
                width=1
            )

    # Stones
    for y in range(HEIGHT):
        for x in range(WIDTH):
            stone = stones[y][x]

            if stone is None:
                continue

            cx = get_coordinates(x)
            cy = get_coordinates(y)

            draw.circle(
                [cx, cy],
                STONE_RADIUS,
                fill=stone.fill,
                outline=stone.outline,
                width=1
            )

    return img

def get_neighbors(x, y):
    if x > 0: yield x - 1, y
    if x < WIDTH - 1: yield x + 1, y
    if y > 0: yield x, y - 1
    if y < HEIGHT - 1: yield x, y + 1

def get_group(x, y, stones):
    colour = stones[y][x]

    if colour is None:
        return set()

    group = set()
    search = deque([(x, y)])

    while search:
        cx, cy = search.popleft()

        if (cx, cy) in group:
            continue

        group.add((cx, cy))

        for nx, ny in get_neighbors(cx, cy):
            if stones[ny][nx] == colour and (nx, ny) not in group:
                search.append((nx, ny))

    return group

def count_group_liberties(group, occupied_stones): 
    return len({ 
        (nx, ny) 
        for gx, gy in group 
        for nx, ny in get_neighbors(gx, gy) 
        if (nx, ny) not in occupied_stones
    })

def remove_group(group, stones, occupied_stones):
    for x, y in group:
        stones[y][x] = None
        occupied_stones.discard((x, y))

def get_move_weights(turn_count, stones, empty_stones, colour, occupied_stones):
    phase = turn_count % StoneColours.SIZE

    generative_factor = max(0.0, (5 - phase) / 5)
    destructive_factor = max(0.0, (phase - 4) / 5)

    move_weights = []

    for cx, cy in empty_stones:

        # ==============================================================
        # 1. Opening (Fuseki)
        # ==============================================================

        dist_x = min(cx, WIDTH - 1 - cx)
        dist_y = min(cy, HEIGHT - 1 - cy)

        weight = 0.05

        if turn_count < 35:
            if dist_x in (2, 3) and dist_y in (2, 3):
                weight += 4.5
            elif dist_x in (2, 3) or dist_y in (2, 3):
                weight += 2.0

        # ==============================================================
        # 2. Global board attraction
        # ==============================================================

        if occupied_stones:
            nearest = min(
                abs(cx - ox) + abs(cy - oy)
                for ox, oy in occupied_stones
            )
            weight += math.exp(-0.6 * nearest)

        # ==============================================================
        # 3. Local neighbourhood
        # ==============================================================

        adjacent_friendly = 0
        adjacent_enemy = 0
        diagonal_friendly = 0

        interelement_bonus = 0.0
        group_bonus = 0.0
        pressure_bonus = 0.0

        friendly_seen = set()
        enemy_seen = set()

        #
        # Orthogonal neighbours
        #

        for nx, ny in get_neighbors(cx, cy):
            neighbour = stones[ny][nx]

            if neighbour is None:
                continue

            #
            # Friendly
            #

            if neighbour == colour:
                adjacent_friendly += 1

                if (nx, ny) not in friendly_seen:
                    group = get_group(nx, ny, stones)
                    friendly_seen |= group

                    group_bonus += (0.6 * math.log2(len(group) + 1))

                    libs = count_group_liberties(group, occupied_stones)

                    group_bonus += (min(libs, 6) * 0.15)

            #
            # Enemy
            #

            else:
                adjacent_enemy += 1

                if (nx, ny) not in enemy_seen:
                    group = get_group(nx, ny, stones)
                    enemy_seen |= group

                    libs = count_group_liberties(group, occupied_stones)

                    if libs == 1:
                        pressure_bonus += 3.0
                    elif libs == 2:
                        pressure_bonus += 1.5
                    elif libs == 3:
                        pressure_bonus += 0.5

            #
            # Elemental relationships
            #

            if StoneColours.GENERATES[colour] == neighbour:
                interelement_bonus += (0.60 * generative_factor)

            elif StoneColours.GENERATES[neighbour] == colour:
                interelement_bonus += (0.30 * generative_factor)

            elif StoneColours.CONTROLS[colour] == neighbour:
                interelement_bonus += (0.60 * destructive_factor)

            elif StoneColours.CONTROLS[neighbour] == colour:
                interelement_bonus -= (0.40 * destructive_factor)

        #
        # Diagonals
        #

        for dx, dy in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            nx = cx + dx
            ny = cy + dy

            if 0 <= nx < WIDTH and 0 <= ny < HEIGHT and stones[ny][nx] == colour:
                diagonal_friendly += 1

        # ==============================================================
        # 4. Tactical scoring
        # ==============================================================

        combat = 1.5 * adjacent_enemy + 0.8 * adjacent_friendly + 0.4 * diagonal_friendly

        #
        # Sheng
        #

        if generative_factor > 0:
            group_bonus += 2.25 * adjacent_friendly * generative_factor

            if adjacent_friendly == 0 and occupied_stones:
                group_bonus += 0.75 * generative_factor

        #
        # Ke
        #

        if destructive_factor > 0:
            combat += 0.75 * adjacent_enemy * destructive_factor

            pressure_bonus *= 1.0 + destructive_factor

            if adjacent_enemy == 0 and occupied_stones:
                combat += 0.5 * destructive_factor

        # ==============================================================
        # Final
        # ==============================================================

        weight += combat + group_bonus + pressure_bonus + interelement_bonus

        move_weights.append(max(weight, 0.01))

    return move_weights

def get_empty_stones(stones):
    return [
        (x, y)
        for y in range(HEIGHT)
        for x in range(WIDTH)
        if stones[y][x] is None
    ]

def capture_adjacent_groups(x, y, colour, stones, occupied_stones):
    checked = set()

    for nx, ny in get_neighbors(x, y):
        if (nx, ny) in checked:
            continue

        enemy = stones[ny][nx]

        if enemy is None or enemy == colour:
            continue

        group = get_group(nx, ny, stones)
        checked.update(group)

        if count_group_liberties(group, occupied_stones) == 0:
            remove_group(group, stones, occupied_stones)

def play_move(x, y, colour, stones, occupied_stones):
    stones[y][x] = colour
    occupied_stones.add((x, y))
    capture_adjacent_groups(
        x,
        y,
        colour,
        stones,
        occupied_stones
    )

frames: list[Image.Image] = []

stones: list[list[Colour | None]] = [[None] * WIDTH for _ in range(HEIGHT)]
occupied_stones = set()

max_turns = 300
turn_count = 0

current_colour = StoneColours.ORDINALS[0]

frames.append(render_board_frame(turn_count, stones))

# Empty board starting point to allow Fuseki to shine
while turn_count < max_turns:
    print(turn_count)
    
    empty_stones = get_empty_stones(stones)
                
    if not empty_stones:
        break     
    
    move_weights = get_move_weights(turn_count, stones, empty_stones, current_colour, occupied_stones)
    turn_count += 1
        
    chosen_move = random.choices(empty_stones, weights=move_weights, k=1)[0]
    px, py = chosen_move
    
    play_move(px, py, current_colour, stones, occupied_stones)
    frames.append(render_board_frame(turn_count, stones))
                    
    current_colour = StoneColours.ORDINALS[turn_count % StoneColours.SIZE]
    
if frames:
    frames[0].save(
        "./Generated Gifs/elemental_goban_simulation.gif",
        save_all=True,
        append_images=frames[1:],
        duration=1000 // 10,   # Milliseconds per frame (lower is faster)
    )
    print(f"Successfully generated animation with {len(frames)} frames!")