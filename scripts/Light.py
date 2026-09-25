import math
import os
import random
from PIL import Image, ImageDraw
import colorsys

class Photon:
    UNIT_CIRCLE = 2 * math.pi
    SPEED = 1
    
    def __init__(self, x: float, y: float, theta: float, wavelength: float, polarity: float):
        self.x = x
        self.y = y
        self.theta = theta
        self.polarity = polarity   
        self._wavelength = wavelength
        self.absorbed = False
        self.reflected = False

    @property 
    def wavelength(self):
        return self._wavelength
    
    @wavelength.setter
    def wavelength(self, other: int):
        """clamps between 380nm and 780nm"""
        self._wavelength = min(max(380, other), 780)
        
    @property 
    def theta(self):
        return math.atan2(self.dy, self.dx)
    
    @theta.setter
    def theta(self, other: float):
        """radians"""
        other %= self.UNIT_CIRCLE
        self.dx = self.SPEED * math.cos(other)
        self.dy = self.SPEED * math.sin(other)
        
    @property
    def nx(self):
        return self.x + self.dx
    
    @property
    def ny(self):
        return self.y + self.dy
        
    def move(self):
        self.x = self.nx
        self.y = self.ny
        
    def check_bound(self, x1, y1, x2, y2):
        return x1 <= self.x < x2 and y1 <= self.y < y2
        
    @property
    def colour(self):
        gamma = 0.8
        intensity_max = 255
        factor = 0.0
        r, g, b = 0.0, 0.0, 0.0

        if 380 <= self._wavelength <= 440:
            r = -(self._wavelength - 440) / (440 - 380)
            g = 0.0
            b = 1.0
        elif 440 < self._wavelength <= 490:
            r = 0.0
            g = (self._wavelength - 440) / (490 - 440)
            b = 1.0
        elif 490 < self._wavelength <= 510:
            r = 0.0
            g = 1.0
            b = -(self._wavelength - 510) / (510 - 490)
        elif 510 < self._wavelength <= 580:
            r = (self._wavelength - 510) / (580 - 510)
            g = 1.0
            b = 0.0
        elif 580 < self._wavelength <= 645:
            r = 1.0
            g = -(self._wavelength - 645) / (645 - 580)
            b = 0.0
        elif 645 < self._wavelength <= 780:
            r = 1.0
            g = 0.0
            b = 0.0

        # Intensity factor adjustment at the edges
        if 380 <= self._wavelength <= 420:
            factor = 0.3 + 0.7 * (self._wavelength - 380) / (420 - 380)
        elif 420 < self._wavelength <= 700:
            factor = 1.0
        elif 700 < self._wavelength <= 780:
            factor = 0.3 + 0.7 * (780 - self._wavelength) / (780 - 700)

        # Gamma correction and intensity scaling
        r = int(round(intensity_max * (r * factor) ** gamma))
        g = int(round(intensity_max * (g * factor) ** gamma))
        b = int(round(intensity_max * (b * factor) ** gamma))

        return (r, g, b)

class PointLight:
    UNIT_CIRCLE = 2 * math.pi
    
    def __init__(self, x: float, y: float, lower_wavelength: float, upper_wavelength: float, ray_count: int):
        self.x = x
        self.y = y
        self.lower_wavelength = lower_wavelength
        self.upper_wavelength = upper_wavelength
        self.ray_count = ray_count
        
    def get_photons(self) -> list[Photon]:
        return [Photon(x=self.x, 
                       y=self.y, 
                       theta=random.uniform(0, self.UNIT_CIRCLE), 
                       wavelength=random.uniform(self.lower_wavelength, self.upper_wavelength), 
                       polarity=random.uniform(0, math.pi)) for _ in range(self.ray_count)]
    
class LaserLight:
    UNIT_CIRCLE = 2 * math.pi
    
    def __init__(self, x: float, y: float, wavelength: float, polarity: float, theta: float, intensity: int):
        self.x = x
        self.y = y
        self.wavelength = wavelength
        self.theta = math.radians(theta - 90)
        self.intensity = intensity
        self.polarity = polarity
        
    def get_photons(self) -> list[Photon]:
        return [Photon(x=self.x, y=self.y, theta=self.theta, wavelength=self.wavelength, polarity=self.polarity) for _ in range(self.intensity)]
    
class SpotLight:
    UNIT_CIRCLE = 2 * math.pi
    
    def __init__(self, x: float, y: float, lower_wavelength: float, upper_wavelength: float, ray_count: int, theta: float, arc: float):
        self.x = x
        self.y = y
        self.lower_wavelength = lower_wavelength
        self.upper_wavelength = upper_wavelength
        self.ray_count = ray_count
        theta = math.radians(theta - 90) #offset so zero degress is up instead of right
        half_arc = math.radians(arc / 2)
        theta_1 = theta + half_arc
        theta_2 = theta - half_arc
        self.lower_theta = min(theta_1, theta_2)
        self.upper_theta = max(theta_1, theta_2)
        
    def get_photons(self) -> list[Photon]:
        return [Photon(x=self.x, 
                       y=self.y, 
                       theta=random.uniform(self.lower_theta, self.upper_theta), 
                       wavelength=random.uniform(self.lower_wavelength, self.upper_wavelength), 
                       polarity=random.uniform(0, math.pi)) for _ in range(self.ray_count)]
    
    def __repr__(self):
        fmt = 'LightSource(x={}, y={}, lower_wavelength={}, upper_wavelength={}, ray_count={}, lower_theta={}, upper_theta={})'
        return fmt.format(self.x, self.y, self.lower_wavelength, self.upper_wavelength, self.ray_count, self.lower_theta, self.upper_theta)
    
class Wall:
    UNIT_CIRCLE = 2 * math.pi
    
    def __init__(self, x1: float, y1: float, x2: float, y2):
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        
    def intersects_path(self, photon: Photon):
        """Checks if the path from (x0, y0) to (x1, y1) intersects this mirror."""
        def ccw(a, b, c):
            return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

        A = (photon.x, photon.y)
        B = (photon.nx, photon.ny)
        C = (self.x1, self.y1)
        D = (self.x2, self.y2)
        
        return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)
    
class Barrier(Wall):
    def __init__(self, x1: float, y1: float, x2: float, y2: float, reflection: float, absorption: float):
        super().__init__(x1, y1, x2, y2)
        self.theta = math.atan2(y1 - y2, x1 - x2) % self.UNIT_CIRCLE
        self.inverse_theta = (self.theta + math.pi) % self.UNIT_CIRCLE
        self.reflection = reflection
        self.absorption = absorption
    
    def hit(self, photon: Photon) -> Photon:
        if super().intersects_path(photon):
            if random.random() <= self.reflection:
                if self.angle_diff(photon.theta, self.theta) < self.angle_diff(photon.theta, self.inverse_theta):
                    photon.theta = 2 * self.theta - photon.theta
                else:
                    photon.theta = 2 * self.inverse_theta - photon.theta
                photon.reflected = True
                
            elif random.random() <= self.absorption: #absorptions destroys it so no angle change
                photon.absorbed = True #TODO angle of refraction
                
            #transmission does not change the photon
            return True
            
        return False

    def angle_diff(self, a: float, b: float):
        return abs((a - b + math.pi) % self.UNIT_CIRCLE - math.pi)
    
    @property
    def colour(self):
        return (255, 255, 255) #TODO generate based on absorption and reflection values

class Polarizer(Wall):
    UNIT_CIRCLE = 2 * math.pi
    
    def __init__(self, x1: float, y1: float, x2: float, y2: float, polarity: float, threshold: float):
        super().__init__(x1, y1, x2, y2)
        self.polarity = math.radians(polarity % 180)
        self.threshold = threshold
        
    def hit(self, photon: Photon) -> Photon:
        if super().intersects_path(photon):
            diff = abs((photon.polarity - self.polarity + math.pi) % math.pi)
            if not diff < self.threshold: 
                photon.absorbed = True
                return False
            
        return True
    
    @property
    def colour(self):
        return (128, 128, 128)

class Filter(Wall):
    def __init__(self, x1: float, y1: float, x2: float, y2: float, min_wavelength: float, max_wavelength: float):
        super().__init__(x1, y1, x2, y2)
        self.min_wavelength = min(min_wavelength, max_wavelength) 
        self.max_wavelength = max(min_wavelength, max_wavelength) 
        
    def hit(self, photon: Photon) -> Photon:
        if super().intersects_path(photon):
            if self.wavelength_in_range(photon):
                return True
            else:
                photon.absorbed = True
                return False
        return True
    
    def wavelength_in_range(self, photon: Photon):
        return self.min_wavelength <= photon.wavelength <= self.max_wavelength
    
    @property
    def colour(self):
        gamma = 0.8
        intensity_max = 255
        factor = 0.0
        r, g, b = 0.0, 0.0, 0.0

        wavelength = (self.min_wavelength + self.max_wavelength) / 2

        if 380 <= wavelength <= 440:
            r = -(wavelength - 440) / (440 - 380)
            g = 0.0
            b = 1.0
        elif 440 < wavelength <= 490:
            r = 0.0
            g = (wavelength - 440) / (490 - 440)
            b = 1.0
        elif 490 < wavelength <= 510:
            r = 0.0
            g = 1.0
            b = -(wavelength - 510) / (510 - 490)
        elif 510 < wavelength <= 580:
            r = (wavelength - 510) / (580 - 510)
            g = 1.0
            b = 0.0
        elif 580 < wavelength <= 645:
            r = 1.0
            g = -(wavelength - 645) / (645 - 580)
            b = 0.0
        elif 645 < wavelength <= 780:
            r = 1.0
            g = 0.0
            b = 0.0

        # Intensity factor adjustment at the edges
        if 380 <= wavelength <= 420:
            factor = 0.3 + 0.7 * (wavelength - 380) / (420 - 380)
        elif 420 < wavelength <= 700:
            factor = 1.0
        elif 700 < wavelength <= 780:
            factor = 0.3 + 0.7 * (780 - wavelength) / (780 - 700)

        # Gamma correction and intensity scaling
        r = int(round(intensity_max * (r * factor) ** gamma))
        g = int(round(intensity_max * (g * factor) ** gamma))
        b = int(round(intensity_max * (b * factor) ** gamma))

        return (r, g, b)

class Portal(Wall):
    UNIT_CIRCLE = 2 * math.pi  # Ensure this exists somewhere

    def __init__(self, x1_1: float, y1_1: float, x2_1: float, y2_1: float,
                       x1_2: float, y1_2: float, x2_2: float, y2_2: float):
        self.x1_1 = x1_1
        self.y1_1 = y1_1
        self.x2_1 = x2_1
        self.y2_1 = y2_1
        self.x1_2 = x1_2
        self.y1_2 = y1_2
        self.x2_2 = x2_2
        self.y2_2 = y2_2

        self.theta_1 = math.atan2(y2_1 - y1_1, x2_1 - x1_1) % self.UNIT_CIRCLE
        self.inverse_theta_1 = (self.theta_1 + math.pi) % self.UNIT_CIRCLE

        self.theta_2 = math.atan2(y2_2 - y1_2, x2_2 - x1_2) % self.UNIT_CIRCLE
        self.inverse_theta_2 = (self.theta_2 + math.pi) % self.UNIT_CIRCLE

        self.colour_1 = tuple(int(c * 255) for c in colorsys.hsv_to_rgb(random.random(), 1, 1))
        self.colour_2 = tuple(255 - c for c in self.colour_1)

    def hit(self, photon: Photon) -> bool:
        if self.intersects_path(photon, self.x1_1, self.y1_1, self.x2_1, self.y2_1):
            return self.transport(
                photon,
                self.x1_1, self.y1_1, self.x2_1, self.y2_1,
                self.x1_2, self.y1_2, self.x2_2, self.y2_2,
                self.theta_1, self.theta_2,
                self.inverse_theta_1, self.inverse_theta_2
            )

        if self.intersects_path(photon, self.x1_2, self.y1_2, self.x2_2, self.y2_2):
            return self.transport(
                photon,
                self.x1_2, self.y1_2, self.x2_2, self.y2_2,
                self.x1_1, self.y1_1, self.x2_1, self.y2_1,
                self.theta_2, self.theta_1,
                self.inverse_theta_2, self.inverse_theta_1
            )

        return False

    def transport(self, photon: Photon,
                  x1_from, y1_from, x2_from, y2_from,
                  x1_to, y1_to, x2_to, y2_to,
                  theta_from, theta_to,
                  inverse_theta_from, inverse_theta_to) -> bool:
        
        dx = x2_from - x1_from
        dy = y2_from - y1_from
        length_squared = dx * dx + dy * dy

        if length_squared == 0:
            return False  # Degenerate portal

        # Relative position t along the from-segment
        t = ((photon.x - x1_from) * dx + (photon.y - y1_from) * dy) / length_squared

        # Optional clamp: prevent overshoot near ends
        t = max(0.0, min(1.0, t))

        # New position on target portal
        photon.x = x1_to + t * (x2_to - x1_to)
        photon.y = y1_to + t * (y2_to - y1_to)

        # Adjust photon angle
        if self.angle_diff(photon.theta, theta_to) > self.angle_diff(photon.theta, inverse_theta_to):
            delta_theta = (theta_from - theta_to) % self.UNIT_CIRCLE
        else:
            delta_theta = (inverse_theta_from - inverse_theta_to) % self.UNIT_CIRCLE

        photon.theta = (photon.theta + delta_theta) % self.UNIT_CIRCLE
        #photon.reflected = True
        return True

    def intersects_path(self, photon: Photon, x1, y1, x2, y2) -> bool:
        """Checks if the line segment intersects the path of the photon (ray)."""
        def ccw(a, b, c):
            return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

        A = (photon.x, photon.y)
        B = (photon.nx, photon.ny)  # Presumed future or direction point
        C = (x1, y1)
        D = (x2, y2)

        return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

    def angle_diff(self, a: float, b: float) -> float:
        """Minimum absolute difference between two angles, wrapped to [0, π]."""
        return abs((a - b + math.pi) % self.UNIT_CIRCLE - math.pi)

if __name__ == '__main__':
    width, height = 100, 100
    iterations = 500
    gif_length = 60
    interval = 5
    
    filePath = os.path.join(os.path.dirname(__file__), 'Generated Images')
    os.makedirs(filePath, exist_ok=True)

    fileName = f'{width}x{height}-light.gif'
    filePath = os.path.join(filePath, fileName)
    
    black = (0, 0, 0)
    
    lights = [SpotLight(x=90, y=10, lower_wavelength=380, upper_wavelength=480, ray_count=16, theta=225, arc=90)]
    walls = [Barrier(x1=0, y1=50, x2=50, y2=100, reflection=0.5, absorption=0.5), Polarizer(0, 0, 100, 100, 90, 0.25), Filter(75, 100, 0, 25, 680, 780)]
    portals = [Portal(x1_1=50, y1_1=0, x2_1=0, y2_1=50, x1_2=100, y1_2=50, x2_2=50, y2_2=100)]
    photons = []
    frames = []
    
    for i in range(iterations):
        if i % interval == 0:
            print(i)
            for light in lights:
                photons.extend(light.get_photons())
        
        img = Image.new('RGB', (width, height), black)
        pixels = img.load()
        remaining_photons = []

        for photon in photons:
            photon.reflected = False
            
            for wall in walls:
                wall.hit(photon)
            for portal in portals:
                portal.hit(photon)
            
            if photon.absorbed:
                continue
            
            if not photon.reflected:
                photon.move()

            if photon.check_bound(0, 0, width, height):
                remaining_photons.append(photon)
                
                pixel = pixels[int(photon.x), int(photon.y)]
                if pixel != black:
                    r1, g1, b1 = pixel
                    r2, g2, b2 = photon.colour
                    pixels[int(photon.x), int(photon.y)] = ((r1 + r2) // 2, (g1 + g2) // 2, (b1 + b2) // 2)
                else:
                    pixels[int(photon.x), int(photon.y)] = photon.colour

        drawing = ImageDraw.Draw(img)
        for wall in walls:
            drawing.line(xy=((int(wall.x1), int(wall.y1)), (int(wall.x2), int(wall.y2))), fill=wall.colour, width=1)
        for light in lights:
            drawing.point((light.x, light.y), (255, 255, 255))
        
        for portal in portals:
            drawing.line(xy=((int(portal.x1_1), int(portal.y1_1)), (int(portal.x2_1), int(portal.y2_1))), fill=portal.colour_1, width=1)
            drawing.line(xy=((int(portal.x1_2), int(portal.y1_2)), (int(portal.x2_2), int(portal.y2_2))), fill=portal.colour_2, width=1)

        frames.append(img)
        photons = remaining_photons
        
    frames[0].save(filePath, save_all=True, append_images=frames[1:], optimize=True, duration=gif_length / iterations, loop=0)