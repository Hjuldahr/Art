from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageFilter

def process_sequence_to_3d_hull(frames_dir, output_path, base_resolution=128):
    """
    True 3D Visual Hull engine with proper non-cubic aspect ratio mapping.
    Stretches the model vertically to prevent blocky widening distortions.
    """
    frames_dir = Path(frames_dir)
    frame_files = sorted(list(frames_dir.glob("angle_*.png")))
    
    if not frame_files:
        print("[ERROR] No angle images found!")
        return

    # 1. Establish the true aspect ratio of your raw source slices
    sample_img = cv2.imread(str(frame_files[0]))
    raw_h, raw_w, _ = sample_img.shape
    aspect_ratio = raw_h / raw_w  # Tall full-body image means aspect_ratio > 1.0

    # 2. Stretch our vertical workspace so it's a tall rectangular prism, not a square cube
    grid_res_x = base_resolution
    grid_res_z = base_resolution
    grid_res_y = int(base_resolution * aspect_ratio)  # Automatically expands vertical height

    print(f"Processing {len(frame_files)} frames.")
    print(f"Workspace dimensions set to: {grid_res_x}x{grid_res_y}x{grid_res_z} (Proportional Grid)")
    
    # Initialize our non-cubic master voxel block of clay
    voxel_matrix = np.ones((grid_res_x, grid_res_y, grid_res_z), dtype=bool)

    # Pre-generate 3D coordinate grids centered around (0,0,0) matching our tall workspace bounds
    lin_x = np.linspace(-1, 1, grid_res_x)
    lin_y = np.linspace(-1, 1, grid_res_y)
    lin_z = np.linspace(-1, 1, grid_res_z)
    X, Y, Z = np.meshgrid(lin_x, lin_y, lin_z, indexing='ij')

    bgdModel = np.zeros((1, 65), np.float64)
    fgdModel = np.zeros((1, 65), np.float64)

    for frame_path in frame_files:
        try:
            angle_deg = int(frame_path.stem.split("_")[1])
        except (IndexError, ValueError):
            continue

        print(f" --> Carving perspective: {angle_deg:03d}° ({frame_path.name})...")
        
        # Standard background segmentation
        img = cv2.imread(str(frame_path))
        h, w, _ = img.shape
        mask = np.zeros((h, w), np.uint8)
        rect = (5, 5, w - 10, h - 10)
        cv2.grabCut(img, mask, rect, bgdModel, fgdModel, 3, cv2.GC_INIT_WITH_RECT)
        silhouette_mask = np.where((mask == 0) | (mask == 2), 0, 255).astype(np.uint8)

        mask_image = Image.fromarray(silhouette_mask)
        eroded_mask = mask_image.filter(ImageFilter.MinFilter(size=3))
        feathered_mask = eroded_mask.filter(ImageFilter.GaussianBlur(radius=1))
        binary_mask = np.array(feathered_mask)
        _, binary_mask_clean = cv2.threshold(binary_mask, 1, 1, cv2.THRESH_BINARY)

        # Centroid alignment lock to center her spine axis
        moments = cv2.moments(binary_mask_clean)
        actual_center_x = moments["m10"] / moments["m00"] if moments["m00"] != 0 else w / 2
        shift_x = (w / 2) - actual_center_x

        translation_matrix = np.float32([[1, 0, shift_x], [0, 1, 0]])
        binary_mask_clean = cv2.warpAffine(binary_mask_clean, translation_matrix, (w, h), flags=cv2.INTER_NEAREST)

        # 3. Y-Axis Rotation
        angle_rad = np.radians(angle_deg)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)
        
        rotated_X = X * cos_a - Z * sin_a
        rotated_Z = X * sin_a + Z * cos_a
        rotated_Y = Y

        # 4. Map back to pixel indices matching our non-cubic workspace sizes
        pixel_x = ((rotated_X + 1) * 0.5 * (grid_res_x - 1)).astype(np.int32)
        pixel_y = (((-rotated_Y + 1) * 0.5) * (grid_res_y - 1)).astype(np.int32)

        # Bounds safety clamping
        valid_indices = (pixel_x >= 0) & (pixel_x < grid_res_x) & (pixel_y >= 0) & (pixel_y < grid_res_y)

        # Resize the 2D mask matrix to map onto our spatial resolution system
        resized_mask = cv2.resize(binary_mask_clean, (grid_res_x, grid_res_y), interpolation=cv2.INTER_NEAREST)

        # 5. Intersect views directly
        current_view_cone = np.zeros_like(voxel_matrix)
        current_view_cone[valid_indices] = resized_mask[pixel_y[valid_indices], pixel_x[valid_indices]]
        voxel_matrix = voxel_matrix & current_view_cone

    # =====================================================================
    # EXPORT PROPORTIONAL 3D POINT CLOUD
    # =====================================================================
    x_indices, y_indices, z_indices = np.where(voxel_matrix)
    num_points = len(x_indices)

    # Retain the independent scale arrays so the coordinates preserve their tall proportions
    x_coords = x_indices - (grid_res_x / 2)
    y_coords = -(y_indices - (grid_res_y / 2))  # Height coordinates span further naturally
    z_coords = z_indices - (grid_res_z / 2)

    with open(output_path, 'w') as f:
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"element vertex {num_points}\n")
        f.write("property float x\n")
        f.write("property float y\n")
        f.write("property float z\n")
        f.write("end_header\n")
        
        for x, y, z in zip(x_coords, y_coords, z_coords):
            f.write(f"{x:.4f} {y:.4f} {z:.4f}\n")

    print(f"\n[COMPLETE] Proportional 3D point cloud successfully exported!")
    print(f"--> Saved to: {output_path}")

# =====================================================================
# RUN BATCH PROCESSOR
# =====================================================================
root = Path(__file__).parent
frames_directory = root / 'Sequence Frames'
output_model_file = root / 'Output Images' / 'reconstructed_body.ply'

process_sequence_to_3d_hull(frames_directory, output_model_file, base_resolution=128)
