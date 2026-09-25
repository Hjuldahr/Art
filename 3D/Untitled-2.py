from pathlib import Path
import cv2
import numpy as np

def slice_uneven_composite(composite_path, output_dir):
    """
    Slices a horizontal strip with irregular spacing by dynamically detecting
    the empty white channels separating the subjects.
    """
    # 1. Load image and extract dimensions
    img = cv2.imread(str(composite_path))
    h, w, _ = img.shape
    
    # 2. Convert to grayscale to evaluate color density maps
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Calculate the minimum pixel value down every single vertical column.
    # If a column is pure white, its minimum value will be 255.
    # If a model exists in that column, the minimum value drops lower.
    column_mins = np.min(gray, axis=0)
    
    # Identify boolean positions where columns are NOT pure white background
    # (Using 250 as a safe cushion for compression noise)
    has_subject = column_mins < 250
    
    # 3. Use findContours on a 1D timeline array to isolate the solid groups
    # This acts like a radar scanning from left to right to map the boundaries
    timeline = has_subject.astype(np.uint8) * 255
    timeline_matrix = np.tile(timeline, (10, 1)) # Extrude to 2D for OpenCV compatibility
    contours, _ = cv2.findContours(timeline_matrix, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Extract the left and right X-coordinates of each unique isolated frame
    bounding_boxes = []
    for contour in contours:
        x, _, box_w, _ = cv2.boundingRect(contour)
        bounding_boxes.append((x, x + box_w))
        
    # Sort boxes left-to-right (OpenCV defaults to scanning backwards)
    bounding_boxes = sorted(bounding_boxes, key=lambda b: b[0])
    
    # 4. Extract and save the dynamic frames
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    total_found = len(bounding_boxes)
    print(f"Detected {total_found} separate models on the sheet via whitespace analysis.")
    
    # Calculate angular steps based on how many frames were actually located
    angle_step = 360 / max(1, total_found - 1)
    
    for i, (x_start, x_end) in enumerate(bounding_boxes):
        # Add a 10-pixel padding safety buffer around the frame boundaries
        pad = 10
        x_min = max(0, x_start - pad)
        x_max = min(w, x_end + pad)
        
        # Crop the tailored vertical window slice
        cropped_frame = img[0:h, x_min:x_max]
        
        # Calculate rotation angle sequence
        angle = int(i * angle_step)
        
        # Save frame sequentially
        out_name = f"angle_{angle:03d}.png"
        cv2.imwrite(str(output_dir / out_name), cropped_frame)
        print(f" --> Extracted: {out_name} (Width: {x_max - x_min}px, Bounds: X:[{x_min}:{x_max}])")

# =====================================================================
# EXECUTION
# =====================================================================
root = Path(__file__).parent
composite_file = root / 'Source Images' / 'istockphoto-178840658-612x612.jpg' 
frames_directory = root / 'Sequence Frames'

slice_uneven_composite(composite_file, frames_directory)
