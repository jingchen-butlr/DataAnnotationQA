"""
Annotation visualization functionality.
"""

import logging
import numpy as np
import cv2
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class AnnotationVisualizer:
    """Visualize annotations on thermal frames."""
    
    # Color mapping for different categories (BGR format for OpenCV)
    CATEGORY_COLORS = {
        'person': (0, 0, 255),      # Red
        'furniture': (255, 0, 0),   # Blue
        'object': (0, 255, 0),      # Green
        'building': (0, 255, 255),  # Yellow
        'environment': (255, 255, 0),  # Cyan
        'appliance': (255, 0, 255), # Magenta
    }
    
    def __init__(self, font_scale: float = 0.5, line_thickness: int = 2, scale_factor: int = 8):
        """
        Initialize visualizer.
        
        Args:
            font_scale: Scale factor for text (will be multiplied by scale_factor)
            line_thickness: Thickness of bounding box lines
            scale_factor: Image upscaling factor (applied before drawing)
        """
        self.base_font_scale = font_scale
        self.scale_factor = scale_factor
        self.font_scale = font_scale * (scale_factor / 8)  # Adjust for scale
        self.line_thickness = max(2, line_thickness * (scale_factor // 4))  # Thicker lines for larger images
        self.font = cv2.FONT_HERSHEY_SIMPLEX
    
    def normalize_frame_for_display(self, frame: np.ndarray, 
                                     vmin: Optional[float] = None,
                                     vmax: Optional[float] = None) -> np.ndarray:
        """
        Normalize thermal frame to 8-bit grayscale image.
        
        Args:
            frame: Input thermal frame in Celsius
            vmin: Minimum value for normalization (auto if None)
            vmax: Maximum value for normalization (auto if None)
            
        Returns:
            8-bit grayscale image
        """
        if vmin is None:
            vmin = np.min(frame)
        if vmax is None:
            vmax = np.max(frame)
        
        # Normalize to 0-255
        normalized = ((frame - vmin) / (vmax - vmin) * 255).astype(np.uint8)
        
        return normalized
    
    def draw_bbox(self, image: np.ndarray, bbox: List[float], 
                  color: Tuple[int, int, int]) -> np.ndarray:
        """
        Draw bounding box on image.
        
        Args:
            image: Input image (BGR)
            bbox: Bounding box [center_x, center_y, width, height] in YOLO format (normalized 0-1)
            color: Box color (BGR)
            
        Returns:
            Image with bounding box drawn
        """
        height, width = image.shape[:2]
        
        # Convert YOLO format (center) to pixel coordinates
        cx_norm, cy_norm, w_norm, h_norm = bbox
        
        # Convert center coordinates to top-left corner
        x_norm = cx_norm - w_norm / 2.0
        y_norm = cy_norm - h_norm / 2.0
        
        # Convert to pixel coordinates
        x = int(x_norm * width)
        y = int(y_norm * height)
        w = int(w_norm * width)
        h = int(h_norm * height)
        
        # Draw rectangle from top-left to bottom-right
        cv2.rectangle(image, (x, y), (x + w, y + h), color, self.line_thickness)
        
        return image
    
    def draw_label(self, image: np.ndarray, bbox: List[float], 
                   label_text: str, color: Tuple[int, int, int]) -> np.ndarray:
        """
        Draw label text near bounding box.
        
        Args:
            image: Input image (BGR)
            bbox: Bounding box [center_x, center_y, width, height] in YOLO format (normalized 0-1)
            label_text: Text to display
            color: Text color (BGR)
            
        Returns:
            Image with label drawn
        """
        height, width = image.shape[:2]
        
        # Convert YOLO format (center) to top-left corner for label placement
        cx_norm, cy_norm, w_norm, h_norm = bbox
        x_norm = cx_norm - w_norm / 2.0
        y_norm = cy_norm - h_norm / 2.0
        
        # Convert to pixel coordinates
        x = int(x_norm * width)
        y = int(y_norm * height)
        
        # Get text size for background
        (text_width, text_height), baseline = cv2.getTextSize(
            label_text, self.font, self.font_scale, 1
        )
        
        # Draw background rectangle
        y_text = max(y - 5, text_height + 5)
        cv2.rectangle(
            image, 
            (x, y_text - text_height - baseline - 2), 
            (x + text_width + 2, y_text + baseline),
            (0, 0, 0),  # Black background
            -1  # Filled
        )
        
        # Draw text
        cv2.putText(
            image,
            label_text,
            (x + 1, y_text - baseline - 1),
            self.font,
            self.font_scale,
            color,
            1,
            cv2.LINE_AA
        )
        
        return image
    
    def draw_timestamp(self, image: np.ndarray, timestamp: float, 
                       frame_idx: int) -> np.ndarray:
        """
        Draw timestamp and frame number on image.
        
        Args:
            image: Input image (BGR)
            timestamp: Frame timestamp
            frame_idx: Frame index
            
        Returns:
            Image with timestamp drawn
        """
        height, width = image.shape[:2]
        
        # Format text
        text = f"Frame {frame_idx} | Time: {timestamp:.3f}s"
        
        # Get text size
        (text_width, text_height), baseline = cv2.getTextSize(
            text, self.font, self.font_scale, 1
        )
        
        # Draw background
        padding = 5
        cv2.rectangle(
            image,
            (padding, padding),
            (padding + text_width + padding, padding + text_height + baseline + padding),
            (0, 0, 0),
            -1
        )
        
        # Draw text
        cv2.putText(
            image,
            text,
            (padding * 2, padding + text_height),
            self.font,
            self.font_scale,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )
        
        return image
    
    def visualize_frame(self, frame: np.ndarray, annotation: Optional[Dict],
                       timestamp: float, frame_idx: int,
                       vmin: Optional[float] = None,
                       vmax: Optional[float] = None) -> np.ndarray:
        """
        Visualize a single frame with annotations.
        
        Args:
            frame: Thermal frame in Celsius
            annotation: Annotation dictionary or None
            timestamp: Frame timestamp
            frame_idx: Frame index
            vmin: Min temperature for normalization
            vmax: Max temperature for normalization
            
        Returns:
            Annotated image (BGR), scaled up by scale_factor
        """
        # Normalize frame to 8-bit grayscale
        gray = self.normalize_frame_for_display(frame, vmin, vmax)
        
        # Convert to BGR for color annotations
        bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        
        # SCALE UP FIRST before drawing text (critical for readability!)
        height, width = bgr.shape[:2]
        scaled_width = width * self.scale_factor
        scaled_height = height * self.scale_factor
        bgr = cv2.resize(bgr, (scaled_width, scaled_height), interpolation=cv2.INTER_NEAREST)
        
        # Now draw annotations on the scaled image
        if annotation and 'annotations' in annotation:
            for ann in annotation['annotations']:
                bbox = ann.get('bbox', [])
                category = ann.get('category', 'unknown')
                subcategory = ann.get('subcategory', '')
                object_id = ann.get('object_id', -1)
                
                # Get color for category
                color = self.CATEGORY_COLORS.get(category, (255, 255, 255))
                
                # Draw bounding box
                bgr = self.draw_bbox(bgr, bbox, color)
                
                # Create label text
                label = f"{category}/{subcategory}\nID:{object_id}"
                # For single line (easier to read on scaled images)
                label_short = f"{category[:3]}/{subcategory[:6]} #{object_id}"
                
                # Draw label
                bgr = self.draw_label(bgr, bbox, label_short, color)
        
        # Draw timestamp
        bgr = self.draw_timestamp(bgr, timestamp, frame_idx)
        
        return bgr
    
    def create_legend(self, categories: Dict[str, int], 
                     width: int = 300, height: int = 200) -> np.ndarray:
        """
        Create a legend image showing category colors.
        
        Args:
            categories: Dictionary mapping category names to counts
            width: Legend width
            height: Legend height
            
        Returns:
            Legend image (BGR)
        """
        # Create black background
        legend = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Title
        cv2.putText(
            legend,
            "Categories:",
            (10, 20),
            self.font,
            self.font_scale,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )
        
        # List categories
        y_offset = 40
        line_height = 20
        
        for category, color in self.CATEGORY_COLORS.items():
            if category in categories or any(category in cat for cat in categories):
                # Draw color box
                cv2.rectangle(legend, (10, y_offset), (30, y_offset + 15), color, -1)
                
                # Draw text
                cv2.putText(
                    legend,
                    category,
                    (40, y_offset + 12),
                    self.font,
                    self.font_scale,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA
                )
                
                y_offset += line_height
        
        return legend

