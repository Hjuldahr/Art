from matplotlib import pyplot, colors
import numpy as np

def cartesian_color_to_HSX(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    # 1. Calculate Hue and normalize to standard [0, 360] range
    h = np.arctan2(b, a)
    np.rad2deg(h, out=h)
    h %= 360.0 
    
    # Normalize to a 0-1 range for a circular boundary
    rho = np.hypot(a, b) / np.sqrt(2.0)
    np.clip(rho, 0.0, 1.0, out=rho)
    
    # X is used as it can mean either lightness or value since its coming from a custom colour space
    x = 0.5 + 0.5 * np.cos(rho * np.pi) 
    s = np.sin(rho * np.pi) 
    
    return np.dstack((h, s, x))

# TODO adapt pixel miner to dual pass Y>X, X>Y pass then render use my custom encoding

# TODO resume working on pass-keeper

def render_color_space(resolution: int = 500):
    # 1. Create a coordinate grid from -1.0 to 1.0
    x = np.linspace(-1.0, 1.0, resolution)
    y = np.linspace(-1.0, 1.0, resolution)
    xx, yy = np.meshgrid(x, y)
    
    hsx_img = cartesian_color_to_HSX(xx, yy)
    
    multipliers = np.array([1.0 / 360.0, 1.0, 1.0], dtype=np.float64)
    hsx_img *= multipliers
    rgb_img = colors.hsv_to_rgb(hsx_img)
    
    pyplot.figure(figsize=(6, 6))
    pyplot.imshow(rgb_img, extent=[-1, 1, -1, 1], origin='lower')
    pyplot.title("Polar Colour")
    pyplot.xlabel("X")
    pyplot.ylabel("Y")
    pyplot.grid(False)
    pyplot.show()

# Run the renderer
if __name__ == "__main__":
    render_color_space()