from __future__ import annotations
import math
import random
from typing import List

from matplotlib import pyplot as plt

PI = math.pi
TAU = 2 * math.pi
SIZE = 1000

class Boid:
    def __init__(self):
        # Position
        self.x = random.uniform(10, SIZE - 10)
        self.y = random.uniform(10, SIZE - 10)
        self.z = random.uniform(10, SIZE - 10)
        
        # Velocity
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-0.5, 0.5)
        self.vz = random.uniform(-0.5, 0.5)
        
        # Max speed
        self.max_speed = 100.0
        
        # Behavior weights and neighbor radius
        self.separation_weight = 1.5
        self.alignment_weight = 1.0
        self.cohesion_weight = 1.0
        self.neighbor_radius = 50.0

    def calculate_heading(self, neighbors: List[Boid, float]):
        if not neighbors:
            return
        
        # Only consider neighbors within radius
        nearest_neighbors = [n for n in neighbors if self.distance(n) < self.neighbor_radius]
        count = len(nearest_neighbors)
        if count == 0:
            return

        # Compute behavior vectors
        sep = self.separation(nearest_neighbors)
        align = self.alignment(nearest_neighbors)
        coh = self.cohesion(nearest_neighbors)

        # Weighted combination
        self.vx += self.separation_weight * sep[0] + self.alignment_weight * align[0] + self.cohesion_weight * coh[0]
        self.vy += self.separation_weight * sep[1] + self.alignment_weight * align[1] + self.cohesion_weight * coh[1]
        self.vz += self.separation_weight * sep[2] + self.alignment_weight * align[2] + self.cohesion_weight * coh[2]

        # Limit speed
        self.limit_speed()

    def separation(self, neighbors: List[Boid]):
        dx = dy = dz = 0
        count = len(neighbors)
        for n in neighbors:
            dx += self.x - n.x
            dy += self.y - n.y
            dz += self.z - n.z
        
        if count > 0:
            dx /= count
            dy /= count
            dz /= count

        # Normalize to keep repulsion strong
        length = math.sqrt(dx**2 + dy**2 + dz**2)
        if length > 0:
            dx /= length
            dy /= length
            dz /= length

        return dx, dy, dz

    def alignment(self, neighbors: List[Boid]):
        avg_vx = avg_vy = avg_vz = 0
        count = len(neighbors)
        for n in neighbors:
            avg_vx += n.vx
            avg_vy += n.vy
            avg_vz += n.vz
        
        if count == 0:
            return 0, 0, 0

        avg_vx /= count
        avg_vy /= count
        avg_vz /= count

        # Steering vector toward average velocity
        return avg_vx - self.vx, avg_vy - self.vy, avg_vz - self.vz

    def cohesion(self, neighbors: List[Boid]):
        center_x = center_y = center_z = 0
        count = len(neighbors)
        for n in neighbors:
            center_x += n.x
            center_y += n.y
            center_z += n.z
        
        if count == 0:
            return 0, 0, 0

        center_x /= count
        center_y /= count
        center_z /= count

        # Steering vector toward center
        dx = center_x - self.x
        dy = center_y - self.y
        dz = center_z - self.z

        # Optional normalization for consistent steering strength
        length = math.sqrt(dx**2 + dy**2 + dz**2)
        if length > 0:
            dx /= length
            dy /= length
            dz /= length

        return dx, dy, dz

    def limit_speed(self):
        speed = math.sqrt(self.vx**2 + self.vy**2 + self.vz**2)
        if speed > self.max_speed:
            factor = self.max_speed / speed
            self.vx *= factor
            self.vy *= factor
            self.vz *= factor

    def update_position(self, dt=1.0):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt
        
        self.x = (0.1 if self.x > SIZE else (SIZE - 0.1 if self.x < 0 else self.x))
        self.y = (0.1 if self.y > SIZE else (SIZE - 0.1 if self.y < 0 else self.y))
        self.z = (0.1 if self.z > SIZE else (SIZE - 0.1 if self.z < 0 else self.z))
        
    def distance(self, other: Boid) -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)
    
    def __repr__(self):
        return f"Boid(pos=({self.x:.2f},{self.y:.2f},{self.z:.2f}), vel=({self.vx:.2f},{self.vy:.2f},{self.vz:.2f}))"

def init_display():
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    scatter = ax.scatter([], [], [], c='blue', marker='o')
    ax.set_xlim(0, SIZE)
    ax.set_ylim(0, SIZE)
    ax.set_zlim(0, SIZE)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    plt.ion()  # interactive mode
    plt.show()
    return fig, ax, scatter

def update_display(scatter, boids, pause=0.01):
    """Update the scatter plot with new boid positions."""
    xs = [b.x for b in boids]
    ys = [b.y for b in boids]
    zs = [b.z for b in boids]
    scatter._offsets3d = (xs, ys, zs)  # update the scatter's data
    plt.pause(pause)
    plt.draw()

boids = [Boid() for _ in range(100)]
fig, ax, scatter = init_display()

plt.ion()
for t in range(1000):
    for boid in boids:
        boid.calculate_heading(boids)
        boid.update_position()
        
    update_display(scatter, boids)