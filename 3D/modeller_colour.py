import base64
import json
from pathlib import Path
import struct
import cv2
import numpy as np
from PIL import Image, ImageFilter
from skimage import measure
from scipy.ndimage import gaussian_filter

def process_sequence_to_3d_hull(frames_dir, output_path, base_resolution=256):
    """
    True 3D Visual Hull engine with proper non-cubic aspect ratio mapping.
    Corrects for dynamic 2D image crop window vertical drift using translation maps.
    """
    frames_dir = Path(frames_dir)
    
    # FIX: Select index [0] from the split stem array to allow proper list sorting
    frame_files = sorted(
        list(frames_dir.glob("*_woman_turnaround.png")), 
        key=lambda p: int(p.stem.split('_')[0].split(';')[0])
    )
    
    if not frame_files:
        print("[ERROR] No angle images found inside the target directory!")
        return

    # 1. Establish the true aspect ratio of your raw source slices
    # Now that frame_files is a valid list, slicing index 0 works perfectly
    sample_img = cv2.imread(str(frame_files[0]))
    raw_h, raw_w, _ = sample_img.shape
    aspect_ratio = raw_h / raw_w  # Tall full-body image means aspect_ratio > 1.0

    # 2. Stretch our vertical workspace so it's a tall rectangular prism, not a square cube
    grid_res_x = base_resolution
    grid_res_z = base_resolution
    grid_res_y = int(base_resolution * aspect_ratio)  # Automatically expands vertical height

    print(f"Processing {len(frame_files)} files from the turnaround sequence.")
    print(f"Workspace dimensions set to: {grid_res_x}x{grid_res_y}x{grid_res_z} (High-Density Proportional Grid)")
    
    # Initialize our non-cubic master voxel arrays
    voxel_matrix = np.ones((grid_res_x, grid_res_y, grid_res_z), dtype=bool)
    
    # 3D color channels data arrays
    color_R = np.zeros_like(voxel_matrix, dtype=np.float32)
    color_G = np.zeros_like(voxel_matrix, dtype=np.float32)
    color_B = np.zeros_like(voxel_matrix, dtype=np.float32)
    view_count = np.zeros_like(voxel_matrix, dtype=np.int32)

    # Generate 3D coordinate grids centered around (0,0,0) matching our tall workspace bounds
    lin_x = np.linspace(-1, 1, grid_res_x)
    lin_y = np.linspace(-1, 1, grid_res_y)
    lin_z = np.linspace(-1, 1, grid_res_z)
    X, Y, Z = np.meshgrid(lin_x, lin_y, lin_z, indexing='ij')

    bgdModel = np.zeros((1, 65), np.float64)
    fgdModel = np.zeros((1, 65), np.float64)

    for frame_path in frame_files:
        try:
            # Unpack your precise filename coordinate markers (Index; Yaw; Pitch)
            i, yaw, pitch = frame_path.stem.split("_")[0].split(';')
            i, yaw, pitch = int(i), int(yaw), int(pitch)
        except (IndexError, ValueError):
            print(f" [SKIPPED] Cannot parse angle markers from filename: {frame_path.name}")
            continue

        print(f" --> Processing Frame [{i+1}/{len(frame_files)}]: Yaw={yaw}° Pitch={pitch}° ({frame_path.name})...")
        
        # Background removal pass
        img = cv2.imread(str(frame_path))
        h, w, _ = img.shape
        mask = np.zeros((h, w), np.uint8)
        rect = (5, 5, w - 10, h - 10)
        cv2.grabCut(img, mask, rect, bgdModel, fgdModel, 3, cv2.GC_INIT_WITH_RECT)
        silhouette_mask = np.where((mask == 0) | (mask == 2), 0, 255).astype(np.uint8)

        # Soft edge filter
        mask_image = Image.fromarray(silhouette_mask)
        eroded_mask = mask_image.filter(ImageFilter.MinFilter(size=3))
        feathered_mask = eroded_mask.filter(ImageFilter.GaussianBlur(radius=1))
        binary_mask = np.array(feathered_mask)
        _, binary_mask_clean = cv2.threshold(binary_mask, 1, 1, cv2.THRESH_BINARY)

        # =====================================================================
        # COMPLETE 2D CENTROID ALIGNMENT (HORIZONTAL + VERTICAL FIX)
        # =====================================================================
        moments = cv2.moments(binary_mask_clean)
        if moments["m00"] != 0:
            actual_center_x = moments["m10"] / moments["m00"]
            actual_center_y = moments["m01"] / moments["m00"]  # Tracks vertical center of mass
        else:
            # FIX: Removed the stray subscripting bracket tokens that caused syntax warnings
            actual_center_x = w / 2
            actual_center_y = h / 2

        # Calculate exact offsets to keep her perfectly locked in the middle of the frame
        shift_x = (w / 2) - actual_center_x
        shift_y = (h / 2) - actual_center_y  # Cancels out the y_target drift from the crop configuration

        # Construct a full 2D Translation matrix including the vertical y-shift
        translation_matrix = np.array([[1, 0, shift_x], 
                                       [0, 1, shift_y]], dtype=np.float32)
        
        binary_mask_clean = cv2.warpAffine(binary_mask_clean, translation_matrix, (w, h), flags=cv2.INTER_NEAREST)
        img_centered = cv2.warpAffine(img, translation_matrix, (w, h), flags=cv2.INTER_LINEAR)

        # 3. Apply the calibrated multi-axis camera tracking transformations
        yaw_rad = np.radians(yaw)
        pitch_rad = np.radians(pitch)
        
        cos_y, sin_y = np.cos(yaw_rad), np.sin(yaw_rad)
        cos_p, sin_p = np.cos(pitch_rad), np.sin(pitch_rad)
        
        rotated_X = X * cos_y - Z * sin_y
        rotated_Z = X * sin_y + Z * cos_y
        rotated_Y = Y

        pitched_X = rotated_X
        pitched_Y = rotated_Y * cos_p + rotated_Z * sin_p   
        pitched_Z = -rotated_Y * sin_p + rotated_Z * cos_p

        # 4. Map back to pixel indices matching our non-cubic workspace sizes
        pixel_x = ((pitched_X + 1) * 0.5 * (grid_res_x - 1)).astype(np.int32)
        pixel_y = (((-pitched_Y + 1) * 0.5) * (grid_res_y - 1)).astype(np.int32)

        # Bounds safety clamping
        valid_indices = (pixel_x >= 0) & (pixel_x < grid_res_x) & (pixel_y >= 0) & (pixel_y < grid_res_y)

        # Resize the 2D matrices to map into your spatial resolution system
        resized_mask = cv2.resize(binary_mask_clean, (grid_res_x, grid_res_y), interpolation=cv2.INTER_NEAREST)
        resized_color = cv2.resize(img_centered, (grid_res_x, grid_res_y), interpolation=cv2.INTER_LINEAR)

        # 5. Intersect views directly
        current_view_cone = np.zeros_like(voxel_matrix)
        current_view_cone[valid_indices] = resized_mask[pixel_y[valid_indices], pixel_x[valid_indices]]
        voxel_matrix = voxel_matrix & current_view_cone

        # Sample RGB textures dynamically
        sampled_colors = resized_color[pixel_y[valid_indices], pixel_x[valid_indices]]
        color_B[valid_indices] += sampled_colors[:, 0]
        color_G[valid_indices] += sampled_colors[:, 1]
        color_R[valid_indices] += sampled_colors[:, 2]
        # FIX: Removed the trailing text markers that generated compilation errors
        view_count[valid_indices] += 1

    export_voxels_to_standard_gltf(voxel_matrix, color_R, color_G, color_B, view_count, output_path)


def export_voxels_to_standard_gltf(voxel_matrix, color_R, color_G, color_B, view_count, output_gltf_path):
    """
    Converts a 3D voxel grid into a smooth, watertight, colorized triangle mesh.
    Saves a universally compatible .gltf file using embedded base64 data strings.
    """
    # Ground shadow safety guard (clips out the bottom 4% shadow pool zone)
    h_limit = int(voxel_matrix.shape[1] * 0.96)
    voxel_matrix[:, h_limit:, :] = False

    # Apply a 3D blur to soften the raw voxel hard bounds
    smoothed_voxels = gaussian_filter(voxel_matrix.astype(float), sigma=1.0)

    # Run Marching Cubes to extract smooth vertices and face connections
    verts, faces, _, _ = measure.marching_cubes(smoothed_voxels, level=0.5)

    print(f"Smooth mesh compiled! Packing {len(verts)} vertices and {len(faces)} faces into base64 streams...")

    # Process and map the averaged color tracks
    final_R = np.zeros_like(color_R, dtype=np.uint8)
    final_G = np.zeros_like(color_G, dtype=np.uint8)
    final_B = np.zeros_like(color_B, dtype=np.uint8)
    
    valid_voxels = view_count > 0
    final_R[valid_voxels] = (color_R[valid_voxels] / view_count[valid_voxels]).astype(np.uint8)
    final_G[valid_voxels] = (color_G[valid_voxels] / view_count[valid_voxels]).astype(np.uint8)
    final_B[valid_voxels] = (color_B[valid_voxels] / view_count[valid_voxels]).astype(np.uint8)

    center_x = voxel_matrix.shape[0] / 2
    center_y = voxel_matrix.shape[1] / 2
    center_z = voxel_matrix.shape[2] / 2

    # Pack vertex parameters into a structured bytearray (16 bytes per vertex: position + color)
    v_buffer = bytearray()
    for vert in verts:
        vx = int(np.clip(vert[0], 0, voxel_matrix.shape[0] - 1))
        vy = int(np.clip(vert[1], 0, voxel_matrix.shape[1] - 1))
        vz = int(np.clip(vert[2], 0, voxel_matrix.shape[2] - 1))
        
        # Positional mappings
        x = float(vx - center_x)
        y = float(vy - center_y)
        z = float(vz - center_z)
        
        # Extract corresponding colors
        r, g, b = final_R[vx, vy, vz], final_G[vx, vy, vz], final_B[vx, vy, vz]
        
        v_buffer.extend(struct.pack("<fffBBBB", x, y, z, r, g, b, 255))

    v_len = len(v_buffer)

    # Pack indices into 32-bit unsigned integers with standard right-side-out winding order
    f_buffer = bytearray()
    for face in faces:
        idx0 = int(face[2])  # Reordered face layout for outward normal calculation
        idx1 = int(face[1])
        idx2 = int(face[0])
        f_buffer.extend(struct.pack("<III", idx0, idx1, idx2))
        
    while len(f_buffer) % 4 != 0:
        f_buffer.extend(b'\x00')
    f_len = len(f_buffer)

    bin_buffer = v_buffer + f_buffer
    b64_data = base64.b64encode(bin_buffer).decode('utf-8')
    data_uri = f"data:application/octet-stream;base64,{b64_data}"

    # Standardized JSON metadata dictionary mapping mapping via native dumps library module
    gltf_dict = {
        "asset": {"version": "2.0"},
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [
            {
                "primitives": [
                    {
                        "attributes": {
                            "POSITION": 0,
                            # NORMAL entry is intentionally removed to trigger native browser shader rendering!
                            "COLOR_0": 1  # Shifts color accessor tracking down to slot index 1
                        },
                        "indices": 2,     # Shifts index accessor tracking down to slot index 2
                        "mode": 4
                    }
                ]
            }
        ],
        "accessors": [
            {"bufferView": 0, "byteOffset": 0, "componentType": 5126, "count": len(verts), "type": "VEC3"},      # Position
            {"bufferView": 0, "byteOffset": 12, "componentType": 5121, "count": len(verts), "type": "VEC4", "normalized": True}, # Color (Offset 12 matches byte stride)
            {"bufferView": 1, "byteOffset": 0, "componentType": 5125, "count": len(faces) * 3, "type": "SCALAR"} # Indices
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": v_len, "byteStride": 16, "target": 34962},  # Packed v_buffer array stride set to 16 bytes
            {"buffer": 0, "byteOffset": v_len, "byteLength": f_len, "target": 34963}                 # GL_ELEMENT_ARRAY_BUFFER
        ],
        "buffers": [
            {"byteLength": len(bin_buffer), "uri": data_uri}
        ]
    }

    # Write out cleanly as a standard, valid text JSON file
    with open(output_gltf_path, 'w') as f:
        json.dump(gltf_dict, f, indent=2)

    print(f"\n[COMPLETE] Standard .gltf file successfully compiled!")
    print(f"--> Saved output model directly to: {output_gltf_path}")

# =====================================================================
# RUN BATCH PROCESSOR
# =====================================================================
root = Path(__file__).parent
frames_directory = root / 'results'
output_model_file = root / 'results' / 'reconstructed_body.gltf'

process_sequence_to_3d_hull(frames_directory, output_model_file, base_resolution=256)