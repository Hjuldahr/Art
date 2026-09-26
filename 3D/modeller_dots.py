import base64
import json
from pathlib import Path
import struct
import cv2
import numpy as np
from PIL import Image
from skimage import measure
from scipy.ndimage import gaussian_filter
from rembg import remove

def get_ai_silhouette(frame_path):
    """
    Uses an AI background extraction model to preserve legs/feet 
    even when they match the studio floor color closely.
    """
    # Load image via PIL for rembg compatibility
    input_image = Image.open(frame_path)
    output_rgba = remove(input_image)
    
    # Convert alpha channel directly into a clean binary mask
    alpha = np.array(output_rgba)[:, :, 3]
    _, binary_mask = cv2.threshold(alpha, 10, 1, cv2.THRESH_BINARY)
    return binary_mask

def process_sequence_to_3d_hull(frames_dir, output_path, base_resolution=256):
    """
    True 3D Visual Hull engine with proper non-cubic aspect ratio mapping.
    Updated to preserve lower extremities using deep-learning segmentation models.
    """
    frames_dir = Path(frames_dir)
    
    # Locate and sort files by indexing marker
    frame_files = sorted(
        frames_dir.glob("shot_*.png"), 
        key=lambda p: int(p.stem.split('_')[1])
    )
    
    if not frame_files:
        print("[ERROR] No angle images found inside the target directory!")
        return

    # Establish the true aspect ratio of your raw source slices
    sample_img = cv2.imread(str(frame_files[0]))
    raw_h, raw_w, _ = sample_img.shape
    aspect_ratio = raw_h / raw_w 

    # Expand the vertical bounds of the rectangular workspace grid
    grid_res_x = base_resolution
    grid_res_z = base_resolution
    grid_res_y = int(base_resolution * aspect_ratio)  

    print(f"Processing {len(frame_files)} files from the turnaround sequence.")
    print(f"Workspace dimensions set to: {grid_res_x}x{grid_res_y}x{grid_res_z}")
    
    voxel_matrix = np.ones((grid_res_x, grid_res_y, grid_res_z), dtype=bool)
    
    # Color tracking spatial structures
    color_R = np.zeros_like(voxel_matrix, dtype=np.float32)
    color_G = np.zeros_like(voxel_matrix, dtype=np.float32)
    color_B = np.zeros_like(voxel_matrix, dtype=np.float32)
    view_count = np.zeros_like(voxel_matrix, dtype=np.int32)

    # 3D Coordinate tracking bounds mapping 
    lin_x = np.linspace(-1, 1, grid_res_x)
    lin_y = np.linspace(-1, 1, grid_res_y)
    lin_z = np.linspace(-1, 1, grid_res_z)
    X, Y, Z = np.meshgrid(lin_x, lin_y, lin_z, indexing='ij')

    for frame_path in frame_files:
        try:
            i, yaw, pitch = frame_path.stem.split('_')[1:]
            i, yaw, pitch = int(i), int(yaw), int(pitch)
        except (IndexError, ValueError):
            print(f" [SKIPPED] Cannot parse angle markers from filename: {frame_path.name}")
            continue

        print(f" --> Processing Frame [{i+1}/{len(frame_files)}]: Yaw={yaw}° Pitch={pitch}°...")
        
        img = cv2.imread(str(frame_path))
        h, w, _ = img.shape
        
        # New AI-driven extraction step instead of raw GrabCut
        binary_mask_clean = get_ai_silhouette(str(frame_path))

        # Centroid Alignment (Horizontal + Vertical Fix)
        moments = cv2.moments((binary_mask_clean * 255).astype(np.uint8))
        if moments["m00"] != 0:
            actual_center_x = moments["m10"] / moments["m00"]
            actual_center_y = moments["m01"] / moments["m00"]  
        else:
            actual_center_x = w / 2
            actual_center_y = h / 2

        shift_x = (w / 2) - actual_center_x
        shift_y = (h / 2) - actual_center_y  

        translation_matrix = np.array([[1, 0, shift_x], 
                                       [0, 1, shift_y]], dtype=np.float32)
        
        binary_mask_clean = cv2.warpAffine(binary_mask_clean, translation_matrix, (w, h), flags=cv2.INTER_NEAREST)
        img_centered = cv2.warpAffine(img, translation_matrix, (w, h), flags=cv2.INTER_LINEAR)

        # Coordinate System projection loops
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

        pixel_x = ((pitched_X + 1) * 0.5 * (grid_res_x - 1)).astype(np.int32)
        pixel_y = (((-pitched_Y + 1) * 0.5) * (grid_res_y - 1)).astype(np.int32)

        valid_indices = (pixel_x >= 0) & (pixel_x < grid_res_x) & (pixel_y >= 0) & (pixel_y < grid_res_y)

        resized_mask = cv2.resize(binary_mask_clean, (grid_res_x, grid_res_y), interpolation=cv2.INTER_NEAREST)
        resized_color = cv2.resize(img_centered, (grid_res_x, grid_res_y), interpolation=cv2.INTER_LINEAR)

        current_view_cone = np.zeros_like(voxel_matrix)
        current_view_cone[valid_indices] = resized_mask[pixel_y[valid_indices], pixel_x[valid_indices]]
        voxel_matrix = voxel_matrix & current_view_cone

        sampled_colors = resized_color[pixel_y[valid_indices], pixel_x[valid_indices]]
        color_B[valid_indices] += sampled_colors[:, 0]
        color_G[valid_indices] += sampled_colors[:, 1]
        color_R[valid_indices] += sampled_colors[:, 2]
        view_count[valid_indices] += 1

    export_voxels_to_standard_gltf(voxel_matrix, color_R, color_G, color_B, view_count, output_path)

def export_voxels_to_standard_gltf(voxel_matrix, color_R, color_G, color_B, view_count, output_gltf_path):
    """
    Converts voxel coordinates to solid geometry and packs output as standard .gltf
    """
    # CRITICAL FIX: Removed the bottom 4% absolute vertical clipper array deletion pass
    # This prevents the feet/calves from being sliced out of the final mesh structure.

    # Soften the voxel boundaries using a slight 3D Gaussian pass
    smoothed_voxels = gaussian_filter(voxel_matrix.astype(float), sigma=1.0)
    verts, faces, _, _ = measure.marching_cubes(smoothed_voxels, level=0.5)

    print(f"Smooth mesh compiled! Packing {len(verts)} vertices and {len(faces)} faces into base64 streams...")

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

    v_buffer = bytearray()
    for vert in verts:
        vx = int(np.clip(vert[0], 0, voxel_matrix.shape[0] - 1))
        vy = int(np.clip(vert[1], 0, voxel_matrix.shape[1] - 1))
        vz = int(np.clip(vert[2], 0, voxel_matrix.shape[2] - 1))
        
        # Scale into spatial coordinate positions
        x = float(vx - center_x)
        y = float(vy - center_y)
        z = float(vz - center_z)
        
        r, g, b = final_R[vx, vy, vz], final_G[vx, vy, vz], final_B[vx, vy, vz]
        v_buffer.extend(struct.pack("<fffBBBB", x, y, z, r, g, b, 255))

    v_len = len(v_buffer)

    f_buffer = bytearray()
    for face in faces:
        idx0, idx1, idx2 = int(face[2]), int(face[1]), int(face[0])
        f_buffer.extend(struct.pack("<III", idx0, idx1, idx2))
        
    while len(f_buffer) % 4 != 0:
        f_buffer.extend(b'\x00')
    f_len = len(f_buffer)

    bin_buffer = v_buffer + f_buffer
    b64_data = base64.b64encode(bin_buffer).decode('utf-8')
    data_uri = f"data:application/octet-stream;base64,{b64_data}"

    gltf_dict = {
        "asset": {"version": "2.0"},
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "COLOR_0": 1}, "indices": 2, "mode": 4}]}],
        "accessors": [
            {"bufferView": 0, "byteOffset": 0, "componentType": 5126, "count": len(verts), "type": "VEC3"},      
            {"bufferView": 0, "byteOffset": 12, "componentType": 5121, "count": len(verts), "type": "VEC4", "normalized": True}, 
            {"bufferView": 1, "byteOffset": 0, "componentType": 5125, "count": len(faces) * 3, "type": "SCALAR"} 
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": v_len, "byteStride": 16, "target": 34962},  
            {"buffer": 0, "byteOffset": v_len, "byteLength": f_len, "target": 34963}                 
        ],
        "buffers": [{"byteLength": len(bin_buffer), "uri": data_uri}]
    }

    with open(output_gltf_path, 'w') as f:
        json.dump(gltf_dict, f, indent=2)

    print(f"\n[COMPLETE] Model saved directly to: {output_gltf_path}")

if __name__ == "__main__":
    root = Path(__file__).parent
    frames_directory = root / 'sequence frames'
    output_model_file = root / 'output images' / 'reconstructed_body.gltf'

    process_sequence_to_3d_hull(frames_directory, output_model_file, base_resolution=256)
