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

def process_sequence_to_3d_hull(frames_dir, output_path, base_resolution=256, camera_distance=4.0):
    """
    Advanced Space Carving Engine using true 3D perspective projection matrices.
    Calibrated to map explicit pixel cropping offsets safely into 3D camera space.
    """
    frames_dir = Path(frames_dir)
    
    frame_files = sorted(
        list(frames_dir.glob("shot_*.png")), 
        key=lambda p: int(p.stem.split('_')[1])
    )
    
    if not frame_files:
        print("[ERROR] No angle images found inside the target directory!")
        return

    # Dimensions matched to your configuration profile
    FRAME_W = 180
    FRAME_H = 400
    X_OFFSET = -4.0   
    Y_OFFSET = 40.0   
    
    aspect_ratio = FRAME_H / FRAME_W 

    grid_res_x = base_resolution
    grid_res_z = base_resolution
    grid_res_y = int(base_resolution * aspect_ratio)  

    print(f"Processing {len(frame_files)} files with 3D camera matrix mapping.")
    print(f"Aspect Ratio: {aspect_ratio:.3f} | Matrix Grid: {grid_res_x}x{grid_res_y}x{grid_res_z}")
    
    voxel_matrix = np.ones((grid_res_x, grid_res_y, grid_res_z), dtype=bool)
    
    color_R = np.zeros_like(voxel_matrix, dtype=np.float32)
    color_G = np.zeros_like(voxel_matrix, dtype=np.float32)
    color_B = np.zeros_like(voxel_matrix, dtype=np.float32)
    view_count = np.zeros_like(voxel_matrix, dtype=np.int32)

    # Define standard proportional 3D space tracking bounds
    lin_x = np.linspace(-1.0, 1.0, grid_res_x)
    lin_y = np.linspace(-aspect_ratio, aspect_ratio, grid_res_y)
    lin_z = np.linspace(-1.0, 1.0, grid_res_z)
    X, Y, Z = np.meshgrid(lin_x, lin_y, lin_z, indexing='ij')
    
    # Flatten the 3D grid points into a 4D homogeneous matrix coordinate tracking array [X, Y, Z, 1]
    points_3d = np.vstack([X.ravel(), Y.ravel(), Z.ravel(), np.ones(X.size)])

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

        # 1. CAMERA INTRINSICS MATRIX (K): Sets the focal length and integrates your pixel offsets
        focal_length = max(w, h) * 1.5  
        K = np.array([
            [focal_length, 0, (w / 2.0) + X_OFFSET],
            [0, focal_length, (h / 2.0) - Y_OFFSET],
            [0, 0, 1.0]
        ], dtype=float)

        # 2. CAMERA EXTRINSICS (R, T): Maps turntable sphere coordinates
        yaw_rad = np.radians(yaw)
        pitch_rad = np.radians(pitch)
        
        # Calculate camera's 3D spatial position relative to the turntable rotation center
        cx = camera_distance * np.cos(pitch_rad) * np.cos(yaw_rad)
        cy = camera_distance * np.cos(pitch_rad) * np.sin(yaw_rad)
        cz = camera_distance * np.sin(pitch_rad)
        camera_pos = np.array([cx, cy, cz])
        
        # Orient the camera to lock its gaze directly on the 3D world origin
        target = np.array([0.0, 0.0, 0.0])
        forward = target - camera_pos
        forward /= np.linalg.norm(forward)
        
        tmp_up = np.array([0.0, 1.0, 0.0]) # Y-axis tracks vertical height
        right = np.cross(forward, tmp_up)
        right /= np.linalg.norm(right)
        up = np.cross(right, forward)
        
        # Construct transformation projection matrix [R | t]
        R = np.vstack([right, up, -forward])
        t = -R @ camera_pos
        Rt = np.column_stack([R, t])
        
        # Complete full 3D to 2D projection matrix calculation (P = K * [R | t])
        P = K @ Rt

        # 3. BACK-PROJECTION AND SPACE CARVING LOOP
        pts_2d_homo = P @ points_3d
        pixel_x_flat = (pts_2d_homo[0] / pts_2d_homo[2]).astype(np.int32)
        pixel_y_flat = (pts_2d_homo[1] / pts_2d_homo[2]).astype(np.int32)

        # Safety envelope validation checks
        in_bounds = (pixel_x_flat >= 0) & (pixel_x_flat < w) & (pixel_y_flat >= 0) & (pixel_y_flat < h)
        
        pixel_occupied = np.zeros(X.size, dtype=bool)
        pixel_occupied[in_bounds] = binary_mask_clean[pixel_y_flat[in_bounds], pixel_x_flat[in_bounds]] == 1
        
        # Update the 3D Voxel Grid array status
        voxel_matrix_flat = voxel_matrix.ravel()
        voxel_matrix_flat &= pixel_occupied

        # Sample and blend texture vertex colors safely
        color_R_flat = color_R.ravel()
        color_G_flat = color_G.ravel()
        color_B_flat = color_B.ravel()
        view_count_flat = view_count.ravel()

        sampled_colors = img[pixel_y_flat[in_bounds], pixel_x_flat[in_bounds]]
        color_B_flat[in_bounds] += sampled_colors[:, 0]
        color_G_flat[in_bounds] += sampled_colors[:, 1]
        color_R_flat[in_bounds] += sampled_colors[:, 2]
        view_count_flat[in_bounds] += 1

    export_voxels_to_standard_gltf(voxel_matrix, color_R, color_G, color_B, view_count, output_path)

def export_voxels_to_standard_gltf(voxel_matrix, color_R, color_G, color_B, view_count, output_gltf_path):
    """ Packs model with correct triangle winding order to fix the inside-out look. """
    if not np.any(voxel_matrix):
        print("[ERROR] Space carving collapsed completely. No geometry left to compile.")
        return

    smoothed_voxels = gaussian_filter(voxel_matrix.astype(float), sigma=1.0)
    verts, faces, _, _ = measure.marching_cubes(smoothed_voxels, level=0.5)

    # Laplacian geometry smoothing pass to polish skin surfaces smoothly
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
        
        # Scale coordinates cleanly using X-width as universal base unit metrics
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
        # Standard counter-clockwise orientation turns the outer surface right-side out
        f_buffer.extend(struct.pack("<III", int(face[0]), int(face[1]), int(face[2])))
        
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

if __name__ == "__main__":
    root = Path(__file__).parent
    frames_directory = root / 'sequence frames'
    output_model_file = root / 'output images' / 'reconstructed_body.gltf'
    process_sequence_to_3d_hull(frames_directory, output_model_file, base_resolution=256)
