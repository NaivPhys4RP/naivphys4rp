"""
Gestalt Perception: Vision Utilities
====================================
This module provides low-level image processing tools and semantic color 
classification logic derived from the original utils.py and filtering.py.

Key Logic:
- Qualia Classification: Maps raw RGB pixels to semantic color categories 
  (Orange, Black, Blue, etc.) using a robust descriptor.
- get_color_dl: A custom CIELab-inspired descriptor (R-G, R-B, G-B, Brightness) 
  designed to be invariant to standard lighting shifts.
- apply_qualia_filter: High-level filtering that simplifies an image into 
  a discrete set of semantic colors (Law of Similarity).

Reference:
Kenfack, F. K. (2026). PhD Dissertation.
"""

import cv2
import numpy as np
from PIL import Image, ImageFilter
from skimage import io, color

class BildVerarbeitung:
    """
    Main processing class for color space transformations and semantic filtering.
    Preserves the 'Qualia' logic used for robust object recognition.
    """
    def __init__(self):
        # Original mapping from semantic labels to visualization pixels
        self.MapQualiaToPixel = {
            "Orange": [255, 168, 0], "Black": [0, 0, 0], "Brown": [119, 90, 48],
            "Silver": [192, 192, 192], "White": [255, 255, 255], "Red": [255, 0, 0],
            "Green": [0, 255, 0], "Blue": [0, 0, 255], "Yellow": [255, 255, 0]
        }
        self.MapQualiaToPixel1 = {}
        self.MapQualiaToPixel_KEYS = list(self.MapQualiaToPixel.keys())
        
        # Pre-calculate descriptors for the reference colors
        for q in self.MapQualiaToPixel_KEYS:
            color_rgb = tuple(self.MapQualiaToPixel[q])
            self.MapQualiaToPixel1[q] = self.get_color_dl(color_rgb)

    def get_color_dl(self, color_tuple, min_value=30, max_value=240):
        """
        Robust CIELab-inspired descriptor from original utils.py.
        Translates RGB into a 4-dimensional vector: (R-G, R-B, G-B, Brightness).
        
        Handles overexposure and underexposure by returning boundary descriptors.
        """
        r, g, b = [float(c) / 255. for c in color_tuple]
        brightness = (r + b + g) / 3
        
        # Thresholding for extreme light conditions
        if max(color_tuple) > max_value: 
            return (0.0, 0.0, 0.0, 1.0) # Overexposed
        if min(color_tuple) < min_value: 
            return (0.0, 0.0, 0.0, 0.0) # Underexposed
            
        return (r - g, r - b, g - b, brightness)

    def get_color_delta(self, c1, c2):
        """
        Original distance logic between Qualia descriptors.
        Uses a combination of cosine similarity (vector orientation) 
        and absolute brightness difference.
        """
        if c1 == c2 == (0.0, 0.0, 0.0, 0.0): 
            return (1.0, 0.0)
        if (0.0, 0.0, 0.0, 0.0) in [c1, c2]: 
            return (np.Inf, np.Inf)
            
        dot = np.dot(c1, c2)
        norm = (np.linalg.norm(c1) * np.linalg.norm(c2))
        cosinus = np.round(dot / norm) if norm != 0 else 0
        
        # Result is (Similarity, Distance)
        return (cosinus, np.arccos(cosinus) + np.abs(c1[3] - c2[3]))

    def apply_qualia_filter(self, img, filter_list, bckg='White'):
        """
        Full implementation of qualia_v2 from utils.py.
        Transforms an RGB image into a simplified semantic color map.
        
        :param img: Input BGR image.
        :param filter_list: List of Qualia keys to consider.
        :param bckg: Default color for pixels not matching the filter.
        """
        rows, cols, dims = img.shape
        img_reshaped = img.reshape([rows * cols, dims])
        
        results = []
        for q in self.MapQualiaToPixel_KEYS:
            # Vectorized delta calculation across all pixels for the current Qualia
            deltas = np.array([self.get_color_delta(self.MapQualiaToPixel1[q], self.get_color_dl(pixel))[1] 
                             for pixel in img_reshaped])
            results.append(deltas.reshape([rows, cols]))
        
        results = np.stack(results, axis=2)
        out_img = np.zeros_like(img)
        
        # Assign best matching Qualia or fallback to background
        for i in range(rows):
            for j in range(cols):
                qualia = self.MapQualiaToPixel_KEYS[np.argmin(results[i, j, :])]
                if qualia not in filter_list:
                    qualia = bckg
                out_img[i, j] = self.MapQualiaToPixel[qualia]
                
        return out_img
