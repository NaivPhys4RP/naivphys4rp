"""
Gestalt Perception: Core Engine
===============================
This module implements the recursive 'Gestalt Distance' algorithm. 
It reconciles the mental world state (X) with real-world observations (Z) 
by calculating the effort of fitting and the error of matching.

Key Logic:
- Recursive group resolution (Law of Similarity/Closure).
- Figure-Ground segmentation using mental regions of attention (ROA).
- Active adjustment between imagination and observation confidence levels.

Reference:
Kenfack, F. K. (2026). PhD Dissertation
"""

import cv2
import numpy as np
from .vision_utils import BildVerarbeitung
from .mtsf import ClusterMTSF
from .matching import *

class GestaltEngine:
    def __init__(self, lambdas, delta):
        """
        Initialize the engine with research-specific weights.
        
        :param lambdas: List of relevancies for MTSFs (Color, Size, Shape, BBox).
        :param delta: Constant penalty for stimuli that cannot be explained by the mental world.
        """
        self.lambdas = lambdas # Relevancies of MTSFs
        self.delta = delta     # Default distance for unfitted stimuli
        self.bv = BildVerarbeitung()

    def compute_distance(self, Z_t, X_t, beta):
        """
        Implementation of Algorithm 1: GestaltDistance
        Calculates the total effort/distance D.
        """
        # 1. Rendering Mental Observation
        Z_t_k = X_t.render() 
        
        # 2-3. Law of Figure-Ground (GetROA & GetForeground)
        mask = X_t.get_roa_mask(Z_t_k)
        Z_t_foreground = cv2.bitwise_and(Z_t, Z_t, mask=mask)
        
        # 4. GetObjectClusters (Similarity, Proximity, Continuity)
        # Uses Canny parameters from your filtering.py: figure_v1
        edges = cv2.Canny(Z_t_foreground, beta['T_lower'], beta['T_upper'])
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        clusters = [ClusterMTSF(c, Z_t_foreground, self.bv) for c in contours]
        
        # 11-12. Law of Closure: Optimal Fit (ArgMin Fit)
        physical_objects = X_t.get_physical_objects()
        fit_table = optimal_fit(physical_objects, clusters)
        
        D = 0
        # 14-26. Iterative Fitting and Matching
        for c in clusters:
            if fit_table[c] is None:
                D += self.delta # Line 16: Unfitted cluster
            else:
                matched_objs = fit_table[c]
                if len(matched_objs) > 1:
                    # Line 19-21: Handle Groups (Recursive Call)
                    new_beta = self._modify_beta(beta)
                    Z_crop = self._crop(Z_t_foreground, c.bbox)
                    X_sub = X_t.filter_subgraph(matched_objs)
                    D += self.compute_distance(Z_crop, X_sub, new_beta)
                else:
                    # Line 23: Vector Distance between MTSFs
                    D += vector_distance(c, matched_objs[0])
        
        # 27-41. Active Adjustment (Imagination <=> Observation)
        self._active_adjustment(X_t, fit_table)
        
        return D

    def _active_adjustment(self, X_t, fit_table):
        """Lines 31-41: Actively adjust imagination based on observation."""
        for relation in X_t.get_relations():
            o1, o2 = relation.o1, relation.o2
            c1 = next((k for k, v in fit_table.items() if v == o1), None)
            c2 = next((k for k, v in fit_table.items() if v == o2), None)
            
            if c1 and c2:
                # Adjust MTSFs based on confidence
                if c1.confidence > o1.confidence:
                    o1.update_mtsf(c1) # Imagination adjusted by observation
                else:
                    c1.update_mtsf(o1) # Observation adjusted by imagination
