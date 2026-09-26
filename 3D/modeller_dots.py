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
    """ Extracts a high-contrast binary mask via rembg. """
    input_image = Image.open(frame_path)
    output_rgba = remove(input_image)
    alpha = np.array(output_rgba)[:, :, 3]
    _, binary_mask = cv2.threshold(alpha, 10, 1, cv2.THRESH_BINARY)
    return binary_mask

def process_sequence_to_3d_hull(frames_dir, output_path, base_resolution=256, thickness_scalar=1.3):
    """
    3D Voxel Carving Engine with independent thickness calibration.
    thickness_scalar: Increase (e.g., 1.5) to widen, decrease (e.g., 1.0) to narrow.
    """
    frames_dir = Path(frames_dir)
    
    frame_files = sorted(
        list(frames_dir.glob("shot_*.png")), 
        key=lambda p: int(p.stem.split('_')[1])
    )
    
    if not frame_files:
        print("[ERROR] No angle images found inside the target directory!")
        return

    FRAME_W = 180
    FRAME_H = 400
    aspect_ratio = FRAME_H / FRAME_W 

    grid_res_x = base_resolution
    grid_res_z = base_resolution
    grid_res_y = int(base_resolution * aspect_ratio)  

    print(f"Processing {len(frame_files)} files.")
    print(f"Aspect Ratio: {aspect_ratio:.3f} | Grid Size: {grid_res_x}x{grid_res_y}x{grid_res_z}")
    
    voxel_matrix = np.ones((grid_res_x, grid_res_y, grid_res_z), dtype=bool)
    
    color_R = np.zeros_like(voxel_matrix, dtype=np.float32)
    color_G = np.zeros_like(voxel_matrix, dtype=np.float32)
    color_B = np.zeros_like(voxel_matrix, dtype=np.float32)
    view_count = np.zeros_like(voxel_matrix, dtype=np.int32)

    # Spatial mapping scaled explicitly by the thickness modifier
    lin_x = np.linspace(-1.0, 1.0, grid_res_x) * thickness_scalar
    lin_y = np.linspace(-aspect_ratio, aspect_ratio, grid_res_y)
    lin_z = np.linspace(-1.0, 1.0, grid_res_z) * thickness_scalar
    X, Y, Z = np.meshgrid(lin_x, lin_y, lin_z, indexing='ij')

    for frame_path in frame_files:
        try:
            parts = frame_path.stem.split('_')
            i, yaw, pitch = int(parts[1]), int(parts[2]), int(parts[3])
        except (IndexError, ValueError):
            print(f" [SKIPPED] Cannot parse angle markers from filename: {frame_path.name}")
            continue

        print(f" --> Processing Frame [{i+1}/{len(frame_files)}]: Yaw={yaw}° Pitch={pitch}°...")
        
        img = cv2.imread(str(frame_path))
        h, w, _ = img.shape
        binary_mask_clean = get_ai_silhouette(str(frame_path))

        yaw_rad = np.radians(yaw)
        pitch_rad = np.radians(pitch)
        
        cos_y, sin_y = np.cos(yaw_rad), np.sin(yaw_rad)
        cos_p, sin_p = np.cos(pitch_rad), np.sin(pitch_rad)
        
        # Robust orthographic tracking matrix math
        rotated_X = X * cos_y - Z * sin_y
        rotated_Z = X * sin_y + Z * cos_y
        rotated_Y = Y

        pitched_X = rotated_X
        pitched_Y = rotated_Y * cos_p + rotated_Z * sin_p   

        pixel_x = ((pitched_X + 1) * 0.5 * (w - 1)).astype(np.int32)
        pixel_y = (((-pitched_Y + 1) * 0.5) * (h - 1)).astype(np.int32)

        valid_indices = (pixel_x >= 0) & (pixel_x < w) & (pixel_y >= 0) & (pixel_y < h)

        current_view_cone = np.zeros_like(voxel_matrix)
        current_view_cone[valid_indices] = binary_mask_clean[pixel_y[valid_indices], pixel_x[valid_indices]]
        voxel_matrix = voxel_matrix & current_view_cone

        sampled_colors = img[pixel_y[valid_indices], pixel_x[valid_indices]]
        color_B[valid_indices] += sampled_colors[:, 0]
        color_G[valid_indices] += sampled_colors[:, 1]
        color_R[valid_indices] += sampled_colors[:, 2]
        view_count[valid_indices] += 1

    export_voxels_to_standard_gltf(voxel_matrix, color_R, color_G, color_B, view_count, output_path)

def export_voxels_to_standard_gltf(voxel_matrix, color_R, color_G, color_B, view_count, output_gltf_path):
    """ Outputs right-side out geometry with correct vertex normals. """
    if not np.any(voxel_matrix):
        print("[ERROR] Space carving collapsed completely. No geometry left to compile.")
        return

    smoothed_voxels = gaussian_filter(voxel_matrix.astype(float), sigma=1.0)
    verts, faces, _, _ = measure.marching_cubes(smoothed_voxels, level=0.5)

    # Geometry relaxation pass to soften vertical ribbing lines
    adjacency = [set() for _ in range(len(verts))]
    for face in faces:
        adjacency[face[0]].update([face[0], face[1], face[2]])
        adjacency[face[1]].update([face[0], face[1], face[2]])
        adjacency[face[2]].update([face[0], face[1], face[2]])
    
    for _ in range(6):
        relaxed_verts = np.copy(verts)
        for idx, neighbors in enumerate(adjacency):
            if neighbors:
                relaxed_verts[idx] = np.mean(verts[list(neighbors)], axis=0)
        verts = 0.5 * verts + 0.5 * relaxed_verts

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

    processed_positions = []
    v_buffer = bytearray()
    
    for vert in verts:
        vx = int(np.clip(vert[0], 0, voxel_matrix.shape[0] - 1))
        vy = int(np.clip(vert[1], 0, voxel_matrix.shape[1] - 1))
        vz = int(np.clip(vert[2], 0, voxel_matrix.shape[2] - 1))
        
        x = float(vx - center_x) / center_x
        y = float(vy - center_y) / center_x  
        z = float(vz - center_z) / center_z
        
        processed_positions.append([x, y, z])
        r, g, b = final_R[vx, vy, vz], final_G[vx, vy, vz], final_B[vx, vy, vz]
        v_buffer.extend(struct.pack("<fffBBBB", x, y, z, r, g, b, 255))

    v_len = len(v_buffer)
    pos_array = np.array(processed_positions)
    min_bounds = pos_array.min(axis=0).tolist()
    max_bounds = pos_array.max(axis=0).tolist()

    f_buffer = bytearray()
    for face in faces:
        # FIXED WINDING: Re-sequenced index elements to push the solid shell right-side out
        f_buffer.extend(struct.pack("<III", int(face[2]), int(face[1]), int(face[0])))
        
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
            {"bufferView": 0, "byteOffset": 0, "componentType": 5126, "count": len(verts), "type": "VEC3", "min": min_bounds, "max": max_bounds},      
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

    print(f"\n[COMPLETE] Proportional model saved to: {output_gltf_path}")

if __name__ == "__main__":
    root = Path(__file__).parent
    frames_directory = root / 'sequence frames'
    output_model_file = root / 'output images' / 'reconstructed_body.gltf'
    process_sequence_to_3d_hull(frames_directory, output_model_file, base_resolution=256, thickness_scalar=1.3)
