from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterable

class Stone:
    __slots__ = ('fill', 'outline')
    
    ordinal_inc = 0
    
    def __init__(self, fill: str, outline: str, ordinal = -1):
        self.ordinal = ordinal
        # for rendering
        self.fill = fill
        self.outline = outline
        
    def copy(self):
        return Stone(self.fill, self.outline, self.ordinal)   
        
    def __eq__(self, value: Stone):
        if not isinstance(value, Stone):
            return False
        return self.ordinal == value.ordinal
    
    def __hash__(self):
        return hash(self.ordinal)

class StoneColours:
    WOOD = Stone('#8CB6A6', '#80B0A0', 0)
    FIRE = Stone('#CD071E', '#C00010', 1)
    EARTH = Stone('#FFB200', '#F0F000', 2)
    METAL = Stone('#E2E5DE', '#E0E0D0', 3)
    WATER = Stone('#161718', '#101010', 4)
    
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

class CandidatePointTypes(Enum):
    CAPTURE = auto()
    SIEGE = auto()
    RALLY = auto()
    BOLSTER = auto()
    CORNER = auto()
    EDGE = auto()
    MISC = auto()

class GobanBoard:
    __slots__ = ('_size', '_intersections', '_occupied', '_neighbour_cache')
    
    _size: int
    _intersections: list[list[Stone | None]]
    _occupied: set[tuple[int, int]]
    _neighbour_cache: dict[tuple[int, int], frozenset[tuple[int, int]]]
    
    def __init__(self, size: int = 19, other: GobanBoard | None = None) -> None:
        if other:
            self._size = other._size
            self._intersections = [row[:] for row in other._intersections]
            self._occupied = set(other._occupied)
            self._neighbour_cache = other._neighbour_cache
        else:
            self._size = size
            self._intersections = [[None] * size for _ in range(size)]
            self._occupied = set()
            self._neighbour_cache = {}
            self._gen_cache()
            
    def _gen_cache(self) -> None:
        for y in range(self._size):
            for x in range(self._size):
                coords = []
                if y > 0:              coords.append((x, y - 1))
                if x > 0:              coords.append((x - 1, y))
                if y < self._size - 1: coords.append((x, y + 1))
                if x < self._size - 1: coords.append((x + 1, y))
                self._neighbour_cache[(x, y)] = frozenset(coords)
            
    def clone(self) -> GobanBoard:
        return GobanBoard(other=self)
    
    def get_friendly_neighbours(self, x: int, y: int) -> list[tuple[int, int]]:
        me = self._intersections[y][x]
        if me is None: 
            return []
        
        results = []
        for nx, ny in self._neighbour_cache[(x, y)]: 
            if self._intersections[ny][nx] == me:
                results.append((nx, ny))
        return results
                
    def get_enemy_neighbours(self, x: int, y: int) -> list[tuple[int, int]]:
        me = self._intersections[y][x]
        if me is None: 
            return []

        results = []
        for nx, ny in self._neighbour_cache[(x, y)]: 
            if (enemy := self._intersections[ny][nx]) is not None and enemy != me:
                results.append((nx, ny))
        return results
    
    def get_liberties(self, x: int, y: int):
        if (x, y) not in self._occupied: return set()
        return self._neighbour_cache[(x, y)] - self._occupied
                
    def count_liberties(self,x,y):
        if (x, y) not in self._occupied: return 0
        return len(self._neighbour_cache[(x, y)] - self._occupied)
    
    def get_group_liberties(self, group: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
        group_liberties = set()
        
        for gxy in group:
            group_liberties |= self._neighbour_cache[gxy] - self._occupied
            
        return group_liberties
                
    def count_group_liberties(self, group: Iterable[tuple[int, int]]) -> int:
        return len(self.get_group_liberties(group))
    
    def get_group(self, x: int, y: int) -> set[tuple[int, int]]:
        if (x, y) not in self._occupied:
            return set()

        group = set()
        frontier = {(x, y)}

        while frontier:
            gxy = frontier.pop()

            if gxy in group:
                continue

            group.add(gxy)
            frontier.update(self.get_friendly_neighbours(*gxy))

        return group
    
    def remove_group(self, group: set[tuple[int, int]]):
        for gx, gy in group:
            self._intersections[gy][gx] = None
        self._occupied -= group
        
    def capture_adjacent_groups(self, x, y) -> int:
        captured = set()
        visited = set()

        for ex, ey in self.get_enemy_neighbours(x, y):
            if (ex, ey) in visited:
                continue

            group = self.get_group(ex, ey)
            visited.update(group)

            if self.count_group_liberties(group) == 0:
                captured.update(group)

        self.remove_group(captured)
        
        return len(captured)
        
    def __getitem__(self, key) -> Stone | None:
        x, y = key
        return self._intersections[y][x]
    
    def __setitem__(self, key, value) -> None:
        x, y = key
        stone = self._intersections[y][x]
        if stone == value:
            return
        self._intersections[y][x] = value
        if value is not None: 
            self._occupied.add(key)
        else: 
            self._occupied.discard(key)
        
    def __delitem__(self, key) -> None:
        x, y = key
        if self._intersections[y][x] is None:
            return
        self._intersections[y][x] = None
        self._occupied.discard(key)
        
    def __eq__(self, value: GobanBoard) -> bool:
        if not isinstance(value, GobanBoard):
            return False
        if self._occupied != value._occupied:
            return False
        
        a = self._intersections
        b = value._intersections
        return all(a[y][x] == b[y][x] for x, y in self._occupied)
    
    def apply_move(self, move: MoveCommand):
        # stone cannot be null so skip setter un-set branch
        x, y = move.xy
        self._intersections[y][x] = move.stone
        self._occupied.add(move.xy)
        
        return self.capture_adjacent_groups(x, y)
    
    def get_candidate_points(self):
        remaining = {
            (x, y)
            for y, row in enumerate(self._intersections)
            for x, stone in enumerate(row)
            if stone is None
        }

        def yield_point(point):
            if point in remaining:
                remaining.remove(point)
                return point
            return None

        # Tactical points: immediate captures
        yield CandidatePointTypes.CAPTURE
        
        enemy_liberties = set()
        for x, y in self._occupied:
            for nx, ny in self.get_enemy_neighbours(x, y):
                group = self.get_group(nx, ny)
                libs = self.get_group_liberties(group)
                if len(libs) == 1:
                    for point in libs:
                        point = yield_point(point)
                        if point is not None:
                            yield point
                else:
                    enemy_liberties.update(libs)

        yield CandidatePointTypes.RALLY
                        
        friendly_liberties = set()
        for x, y in self._occupied:
            for nx, ny in self.get_friendly_neighbours(x, y):
                group = self.get_group(nx, ny)
                libs = self.get_group_liberties(group)
                if len(libs) == 1:
                    for point in libs:
                        point = yield_point(point)
                        if point is not None:
                            yield point
                else:
                    friendly_liberties.update(libs)

        # Tactical points: normal liberties
        yield CandidatePointTypes.SIEGE
        
        remaining -= enemy_liberties
        yield from enemy_liberties

        yield CandidatePointTypes.BOLSTER
                
        remaining -= friendly_liberties
        yield from friendly_liberties
        
        limit = self._size - 1

        # Corners
        yield CandidatePointTypes.CORNER
        
        for corner in (
            (0, 0),
            (limit, 0),
            (0, limit),
            (limit, limit)
        ):
            point = yield_point(corner)
            if point is not None:
                yield point

        # Edges (clockwise)
        yield CandidatePointTypes.EDGE
        
        for x in range(1, limit):
            point = yield_point((x, 0))
            if point is not None:
                yield point

        for y in range(1, limit):
            point = yield_point((limit, y))
            if point is not None:
                yield point

        for x in range(limit - 1, 0, -1):
            point = yield_point((x, limit))
            if point is not None:
                yield point

        for y in range(limit - 1, 0, -1):
            point = yield_point((0, y))
            if point is not None:
                yield point

        # Remaining points
        yield CandidatePointTypes.MISC
        
        yield from remaining

class MoveResultType(Enum):
    PASS = auto()
    LEGAL = auto()
    OUT_OF_BOUNDS = auto()
    OCCUPIED = auto()
    SUICIDE = auto()
    KO = auto()

@dataclass(frozen=True)
class MoveCommand:
    xy: tuple[int, int] | None
    stone: Stone
    
@dataclass(frozen=True)
class MoveResultData:
    result: MoveResultType
    captures: int = 0
    liberties: int = 0
    group: None | frozenset[tuple[int,int]] = None
    
class GoGame:
    def __init__(self, size):
        self.size = size
        self.present = GobanBoard(size)
        self.ko = None
        self.turn = 0
    
    def perform_play(self, move: MoveCommand):
        if move.xy is None:
            self.ko = None
            self.turn += 1
            return MoveResultData(MoveResultType.PASS)
        
        x, y = move.xy
        
        if not (0 <= x < self.size and 0 <= y < self.size):
            return MoveResultData(MoveResultType.OUT_OF_BOUNDS)
        
        # if occupied, disallow
        if self.present[x, y] is not None:
            return MoveResultData(MoveResultType.OCCUPIED)
        
        past = self.present
        sandbox = past.clone()
        captures = sandbox.apply_move(move)
        
        # if it captures, allow risky move
        if captures > 0:
            # if the capture reproduces the previous state, disallow
            if self.ko is not None and sandbox == self.ko:
                return MoveResultData(MoveResultType.KO, captures=captures)
        
        # if it is surrounded but did not capture, disallow suicide move
        group = frozenset(sandbox.get_group(x, y))
        liberties = sandbox.count_group_liberties(group)
        if liberties == 0:
            return MoveResultData(MoveResultType.SUICIDE, captures=captures, group=group)
        
        self.ko = past
        self.present = sandbox
        self.turn += 1
        
        return MoveResultData(MoveResultType.LEGAL, group=group, captures=captures, liberties=liberties)
    
board = GobanBoard()
print([*board.get_candidate_points()])