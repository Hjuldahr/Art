from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np

lower_threshold = 121
upper_threshold = 164

root = Path(__file__).parent
front_img_path = root / 'Source Images' / 'istockphoto-1455864983-612x612.jpg'
side_img_path = root / 'Source Images' / 'istockphoto-1455864984-612x612.jpg'

front_img = Image.open(front_img_path).convert('RGBA')
#side_img = Image.open(side_img_path).convert('RGBA')

data = np.array(front_img)
rgb = data[:, :, 0:3]

# 1. Dynamically sample a 10x10 pixel block from all four corners
top_left = rgb[0:10, 0:10]
top_right = rgb[0:10, -10:]
bottom_left = rgb[-10:, 0:10]
bottom_right = rgb[-10:, -10:]

# 2. Combine the corner samples into a single background reference pool
bg_samples = np.concatenate(
    [top_left, top_right, bottom_left, bottom_right], axis=0
)

# 3. Dynamically calculate the safe lower and upper limits based on actual background pixels
# We add a small tolerance cushion (e.g., +/- 15) to account for mid-screen gradients
lower_threshold = np.min(bg_samples, axis=(0, 1)) - 15
upper_threshold = np.max(bg_samples, axis=(0, 1)) + 15

# 4. Run your exact mask logic with the calculated values
background_mask = np.all(
    (rgb > lower_threshold) & (rgb < upper_threshold), axis=-1
)
data[:, :, 3] = np.where(background_mask, 0, data[:, :, 3])

alpha = data[:, :, 3]

# 3. Create a PIL image of just your alpha mask
mask = Image.fromarray(alpha)

# 4. Erode the mask (shave 1-2 pixels off the edge to eat away the black halo)
# MinFilter finds the minimum alpha value in a 3x3 grid, shrinking the visible edge slightly
eroded_mask = mask.filter(ImageFilter.MinFilter(size=3))

# 5. Feather the mask (add a tiny blur so the hair transitions smoothly)
feathered_mask = eroded_mask.filter(ImageFilter.GaussianBlur(radius=1))

# 6. Inject the cleaned mask back into your image
data[:, :, 3] = np.array(feathered_mask)

# Save or show the polished cutout
Image.fromarray(data).show()

#fil = front_img.filter(ImageFilter.FIND_EDGES())
#fil.show()