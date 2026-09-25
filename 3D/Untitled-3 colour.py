import base64
import json
from pathlib import Path
import struct
import cv2
import numpy as np
from PIL import Image, ImageFilter
from skimage import measure
from scipy.ndimage import gaussian_filter

def process_sequence_to_3d_hull(frames_dir, output_path, base_resolution=128):
    """
    True 3D Visual Hull engine with proper non-cubic aspect ratio mapping.
    Stretches the model correctly without flattening or distortion.
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

    print(f"Processing {len(frame_files)} files.")
    print(f"Workspace dimensions set to: {grid_res_x}x{grid_res_y}x{grid_res_z} (Proportional Grid)")
    
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

    for i, frame_path in enumerate(frame_files):
        try:
            angle_deg = int(frame_path.stem.split("_")[1])
        except (IndexError, ValueError):
            print(f" [SKIPPED] Cannot parse angle from filename: {frame_path.name}")
            continue

        print(f" --> Processing Frame [{i+1}/{len(frame_files)}]: {angle_deg:03d}° ({frame_path.name})...")
        
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

        # Centroid alignment matrix calculation
        moments = cv2.moments(binary_mask_clean)
        actual_center_x = moments["m10"] / moments["m00"] if moments["m00"] != 0 else w / 2
        shift_x = (w / 2) - actual_center_x

        translation_matrix = np.array([[1, 0, shift_x], 
                                       [0, 1, 0]], dtype=np.float32)
        binary_mask_clean = cv2.warpAffine(binary_mask_clean, translation_matrix, (w, h), flags=cv2.INTER_NEAREST)
        img_centered = cv2.warpAffine(img, translation_matrix, (w, h), flags=cv2.INTER_LINEAR)

        # 3. Apply the true Y-axis rotation matrix mapping
        angle_rad = np.radians(angle_deg)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)
        
        rotated_X = X * cos_a - Z * sin_a
        rotated_Z = X * sin_a + Z * cos_a
        rotated_Y = Y # Height maps cleanly since our meshgrid matches the image layout

        # 4. Map back to pixel indices matching our non-cubic workspace sizes
        pixel_x = ((rotated_X + 1) * 0.5 * (grid_res_x - 1)).astype(np.int32)
        pixel_y = (((-rotated_Y + 1) * 0.5) * (grid_res_y - 1)).astype(np.int32)

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
        view_count[valid_indices] += 1

    export_voxels_to_standard_gltf(voxel_matrix, color_R, color_G, color_B, view_count, output_path)

def export_voxels_to_standard_gltf(voxel_matrix, color_R, color_G, color_B, view_count, output_gltf_path):
    """
    Converts a 3D voxel grid into a smooth, watertight, colorized triangle mesh.
    Saves a universally compatible .gltf file using embedded base64 data strings.
    """
    # 1. Apply a 3D blur to soften the raw voxel hard bounds
    smoothed_voxels = gaussian_filter(voxel_matrix.astype(float), sigma=1.0)

    # 2. Run Marching Cubes to extract smooth vertices, face connections, and true normals
    verts, faces, normals, _ = measure.marching_cubes(smoothed_voxels, level=0.5)

    print(f"Smooth mesh compiled! Packing {len(verts)} vertices and {len(faces)} faces into base64 streams...")

    # 3. Process and map the averaged color tracks
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

    # 4. Pack vertex parameters into a structured bytearray
    v_buffer = bytearray()
    for idx, vert in enumerate(verts):
        vx = int(np.clip(vert[0], 0, voxel_matrix.shape[0]-1))
        vy = int(np.clip(vert[1], 0, voxel_matrix.shape[1]-1))
        vz = int(np.clip(vert[2], 0, voxel_matrix.shape[2]-1))
        
        # Positional mappings
        x = float(vx - center_x)
        y = float(vy - center_y)
        z = float(vz - center_z)
        
        # Extract corresponding colors
        r, g, b = final_R[vx, vy, vz], final_G[vx, vy, vz], final_B[vx, vy, vz]
        
        # Pack precisely (3 floats for position + 4 unsigned chars for color = 16 bytes per vertex)
        # Stripping out the normals makes the data stream drastically lighter and faster to read!
        v_buffer.extend(struct.pack("<fffBBBB", x, y, z, r, g, b, 255))

    v_len = len(v_buffer)

    # 5. Pack indices into 32-bit unsigned integers
    f_buffer = bytearray()
    for face in faces:
        # Swap indices 0 and 2 to force the surface normals to point outwards
        idx0 = int(face[2])  # Reverse the sequence!
        idx1 = int(face[1])
        idx2 = int(face[0])
        
        f_buffer.extend(struct.pack("<III", idx0, idx1, idx2))
        
    while len(f_buffer) % 4 != 0:
        f_buffer.extend(b'\x00')
    f_len = len(f_buffer)

    bin_buffer = v_buffer + f_buffer
    b64_data = base64.b64encode(bin_buffer).decode('utf-8')
    data_uri = f"data:application/octet-stream;base64,{b64_data}"

    # =====================================================================
    # 6. UPDATED CLEAN GLTF METADATA DICTIONARY
    # =====================================================================
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
        json.dump(gltf_dict, f, indent=4)

    print(f"\n[COMPLETE] Standard .gltf file successfully compiled!")
    print(f"--> Saved output model directly to: {output_gltf_path}")

# =====================================================================
# RUN BATCH PROCESSOR
# =====================================================================
root = Path(__file__).parent
frames_directory = root / 'Sequence Frames'
output_model_file = root / 'Output Images' / 'reconstructed_body.gltf'

process_sequence_to_3d_hull(frames_directory, output_model_file, base_resolution=256)