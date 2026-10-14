"""
Gestalt Perception: MTSF Extraction
===================================
This module handles the extraction of Minimal Transparent Semantic Features (MTSFs) 
from sensory observations. It implements the "Bottom-Up" phase of the 
Gestalt Distance algorithm.

Key Logic:
- Law of Similarity & Proximity: Clustering pixels via edge detection (Canny).
- Law of Praegnanz: Simplification of clusters into Bounding Boxes.
- Robust Color (Qualia): Translation of RGB values into semantic CIELab/DL descriptors.
- Shape Complexity: Calculation of spatial distribution (isoperimetric quotient).

Reference:
Kenfack, F. K. (2026). PhD Dissertation.
"""

import cv2
import numpy as np
from .vision_utils import BildVerarbeitung

class MTSFExtractor:
    """
    Utility class for high-level extraction tasks on the observation image Z.
    Derived from logic in filtering.py and utils.py.
    """
    def __init__(self):
        self.bv = BildVerarbeitung()

    def get_object_clusters(self, image, beta):
        """
        Groups pixels into clusters based on edges.
        Corresponds to Line 4 of Algorithm 1.
        
        :param image: The foreground-masked image Z_t.
        :param beta: Threshold parameters for Canny (Similarity/Continuity).
        """
        edges = cv2.Canny(image, beta['T_lower'], beta['T_upper'])
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours

    def get_bbox(self, cluster):
        """
        Law of Praegnanz: Simplifies a complex contour into a primary BBox.
        Corresponds to Line 6 of Algorithm 1.
        """
        x, y, w, h = cv2.boundingRect(cluster)
        return [x, y, x + w, y + h]

    def get_simple_color(self, image, cluster_mask):
        """
        Determines the semantic color (Qualia) of a cluster.
        Corresponds to Line 7 of Algorithm 1.
        """
        avg_color = cv2.mean(image, mask=cluster_mask)[:3]
        return self.bv.get_color_dl(avg_color)


class ClusterMTSF:
    """
    Data structure representing the semantic attributes of an observed cluster C.
    Implements the feature vector computation in Lines 5-10 of Algorithm 1.
    """
    def __init__(self, contour, image, processor):
        """
        :param contour: The OpenCV contour of the cluster.
        :param image: The image data for color extraction.
        :param processor: An instance of BildVerarbeitung for CIELab logic.
        """
        self.contour = contour
        
        # Law of Praegnanz: Trivial Bounding Box
        # x, y, w, h
        self.bbox = cv2.boundingRect(contour) 
        
        # COLOR: Classification based on robust CIELab logic from qualia_v2
        mask = np.zeros(image.shape[:2], dtype="uint8")
        cv2.drawContours(mask, [contour], -1, 255, -1)
        mean_color = cv2.mean(image, mask=mask)[:3]
        self.color = processor.get_color_dl(mean_color)
        
        # SIZE: Area calculation from pixels
        self.size = cv2.contourArea(contour)
        
        # SHAPE: Spatial distribution and complexity
        self.shape = self._get_shape_complexity(contour)

        # Confidence used for Active Adjustment (Lines 31-41)
        self.confidence = 1.0 # Default observation confidence

    def _get_shape_complexity(self, cnt):
        """
        Calculates the circularity/complexity of the shape.
        A circle yields ~1.0; fragmented edges yield lower values.
        """
        perimeter = cv2.arcLength(cnt, True)
        area = cv2.contourArea(cnt)
        if perimeter == 0:
            return 0
        return (4 * np.pi * area) / (perimeter**2)
