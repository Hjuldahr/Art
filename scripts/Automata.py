import random

GRID_WIDTH = 16
GRID_HEIGHT = 16
DELTAS = ((-1,-1), (0,-1), (1,-1), (-1,0), (1,0), (-1,1), (0,1), (1,1))

ITERATIONS = 1000
MAX_LIFESPAN = 2

x, y = random.randrange(GRID_WIDTH), random.randrange(GRID_HEIGHT)

grid = [[0] * GRID_WIDTH for _ in range(GRID_HEIGHT)]

occupied = set([(x, y)])
grid[y][x] = True

for i in range(ITERATIONS):
    for xy in list(occupied):
        # RANDOM delay for mitosis
        
        x, y = xy
        available = []
        
        for dx, dy in DELTAS:
            nxy = ((x + dx) % GRID_WIDTH, (y + dy) % GRID_HEIGHT)
            if nxy not in occupied:
                available.append(nxy)
        
        grid[y][x] = 0
        occupied.discard(xy)
        
        next_xy = random.sample(available, min(max(0, len(available)), 2))
        occupied.update(next_xy)
        
        for (nx, ny) in next_xy:
            grid[ny][nx] = (grid[ny][nx] + 1) % MAX_LIFESPAN
            
    for row in grid:
        print(''.join('#' if cell > 0 else ' ' for cell in row))
        
    input()