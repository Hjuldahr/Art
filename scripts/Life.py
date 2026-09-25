import random

def SeedCells(width, height, density = 0.5):
    pixels = []
    
    for _ in range(height):
        row = []
        for _ in range(width):
            if random.random() < density:
                row.append(random.randrange(1, 11))
            else:
                row.append(0)
        pixels.append(row)
        
    return pixels

def Iterate(width, height, cells, cells_configs):
    all_adjacent_cells = []
    
    off_width = width - 1
    off_height = height - 1
    
    for y in range(height):
        row = []
        for x in range(width):
            adjacent_cells = []
            
            if y > 0: # Up
                cell = cells[y-1][x]
                if cell != 0:
                    adjacent_cells.append(cell)
            if x < off_width and y > 0: # Up Right
                cell = cells[y-1][x+1]
                if cell != 0:
                    adjacent_cells.append(cell)
            if x < off_width: # Right
                cell = cells[y][x+1]
                if cell != 0:
                    adjacent_cells.append(cell)
            if x < off_width and y < off_height: # Down Right
                cell = cells[y+1][x+1]
                if cell != 0:
                    adjacent_cells.append(cell)
            if y < off_height: # Down
                cell = cells[y+1][x]
                if cell != 0:
                    adjacent_cells.append(cell)
            if x > 0 and y < off_height: # Down Left
                cell = cells[y+1][x-1]
                if cell != 0:
                    adjacent_cells.append(cell)
            if x > 0: # Left
                cell = cells[y][x-1]
                if cell != 0:
                    adjacent_cells.append(cell)
            if x > 0 and y > 0: # Up Left
                cell = cells[y-1][x-1]
                if cell != 0:
                    adjacent_cells.append(cell)
            
            row.append(adjacent_cells)
        all_adjacent_cells.append(row)
        
        """
        current_cell = cells[y][x]
        low, high = cells_configs[current_cell]
        adjacent_cell_count = len(adjacent_cells)
        
        if adjacent_cell_count < low:
            cells[y][x] = 0
        elif low <= adjacent_cell_count <= high:
            continue
        elif adjacent_cell_count > high:
            cells[y][x] = 0
        elif adjacent_cell_count == high:
            cells[y][x] = -1 #replace with proper logic
        """

width = 100
height = 100

cells_configs = {i: sorted([random.randrange(1, 8), random.randrange(1, 8)]) for i in range(2, 11)}
cells_configs[1] = [2, 3]

cells = SeedCells(width, height)
Iterate(width, height, cells, cells_configs)