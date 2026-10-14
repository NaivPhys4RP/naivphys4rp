"""
Gestalt Perception: Matching & Correspondence
=============================================
This module handles the 'Law of Closure' and 'Semantic Matching' phases 
of the Gestalt Distance algorithm.

It provides logic for:
- Optimal Correspondence (ArgMin Fit): Solving the assignment problem 
  between mental hypotheses and observed stimuli using the Hungarian Algorithm.
- Weighted MTSF Distance: Calculating semantic error based on Color (CIELab Qualia), 
  Shape, Size, and Bounding Boxes.
- CIELab Qualia Delta: A robust color distance metric refined from utils.py.

Reference:
Kenfack, F. K. (2026). PhD Dissertation.
"""

import numpy as np
from scipy.optimize import linear_sum_assignment

def optimal_fit(mental_objects, clusters, lambdas, delta):
    """
    Implementation of ArgMin(Fit(So, Clusters)).
    Strictly follows the Law of Closure (Algorithm 1, Line 12).
    
    Maps physical objects from the mental world to detected image clusters 
    to minimize global matching error.
    """
    fit_table = {cluster: None for cluster in clusters}
    
    if not mental_objects or not clusters:
        return fit_table

    # 1. Construct the Cost Matrix (Rows = Mental Objects, Cols = Observed Clusters)
    cost_matrix = np.zeros((len(mental_objects), len(clusters)))

    for i, m_obj in enumerate(mental_objects):
        for j, cluster in enumerate(clusters):
            # Calculate the MTSF vector distance using research-specific weights
            cost = vector_distance(cluster.MTSF, m_obj.MTSF, lambdas)
            cost_matrix[i, j] = cost

    # 2. Solve the Assignment Problem (Hungarian Algorithm)
    # Minimizes the sum of matching costs globally across the scene
    obj_indices, cluster_indices = linear_sum_assignment(cost_matrix)

    # 3. Populate FitTable based on optimal assignments
    matched_clusters = set()
    for obj_idx, clus_idx in zip(obj_indices, cluster_indices):
        cost = cost_matrix[obj_idx, clus_idx]
        
        # Line 16 Logic: Only assign if fit is better than the penalty delta
        if cost < delta:
            cluster = clusters[clus_idx]
            mental_obj = mental_objects[obj_idx]
            
            # Group support: Initialize or append to the cluster's object list
            if fit_table[cluster] is None:
                fit_table[cluster] = [mental_obj]
            else:
                fit_table[cluster].append(mental_obj)
            
            matched_clusters.add(clus_idx)

    return fit_table


def vector_distance(cluster_mtsfs, mental_mtsfs, weights):
    """
    Computes weighted distance between MTSF vectors.
    Strictly follows Algorithm 1, Line 23.
    """
    # cluster_mtsfs: [Color_Vector, Size_Scalar, Shape_Complexity, BBox_Vector]
    dist = 0
    
    # 1. Color Distance: Integrated from CIELab/Qualia logic in utils.py
    # weights[0] corresponds to lambda_color
    dist += weights[0] * compute_qualia_delta(cluster_mtsfs[0], mental_mtsfs[0])
    
    # 2. Geometry Distances: Size, Shape, and Bounding Box
    for i in range(1, len(weights)):
        # Standardized Euclidean distance for structural features
        diff = np.linalg.norm(cluster_mtsfs[i] - mental_mtsfs[i])
        dist += weights[i] * diff
        
    return dist


def compute_qualia_delta(c1, c2):
    """
    Robust Color Delta.
    Refined implementation of getColorDelta from utils.py.
    Uses Cosine similarity for orientation and absolute difference for brightness.
    """
    if np.array_equal(c1, c2): 
        return 0.0
        
    # Calculate similarity between color descriptors
    norm_product = (np.linalg.norm(c1) * np.linalg.norm(c2)) + 1e-6
    cos_sim = np.dot(c1, c2) / norm_product
    
    # Measure difference in perceived brightness
    brightness_diff = np.abs(c1[3] - c2[3])
    
    # Return combined angular distance and brightness error
    return np.arccos(np.clip(cos_sim, -1, 1)) + brightness_diff
