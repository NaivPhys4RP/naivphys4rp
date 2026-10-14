# 🧠 Gestalt Perception

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](#)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](#)
[![Field: Cognitive Robotics](https://img.shields.io/badge/Field-Cognitive%20Robotics-orange.svg)](#)

**Gestalt Perception** is a Python framework for robust robotic state estimation and object recognition under uncertainty (transparency, reflections, and occlusion). Unlike traditional passive filtering, this library implements an **Active Fitting Process** based on Gestalt psychology to reconcile mental "expectations" with fragmented real-world sensory observations.

---

## 🔬 Mathematical Philosophy

The package addresses the **Perception Paradox**, where comparing two observations is often more complex than the interpretation of the observations themselves. 

### The Paradox
Formally, let $\mathbb{C}$ be complexity, $\mathbb{I}$ interpretation, and $\mathbb{A}$ semantic matching:

$$\mathbb{C}(\mathbb{D}(O_i,O_j)) \approx \mathbb{C}(\mathbb{I}(O_i)) + \mathbb{C}(\mathbb{I}(O_j)) + \mathbb{C}(\mathbb{A}(S_i,S_j))$$

### The Gestalt Distance
The core metric, **Gestalt Distance** ($D$), is defined as the addition of the **execution complexity of the gestalt fitting algorithm** (effort) and the **matching error**:

$$D(Z_t, X_t^{(k)}) = \text{Effort}(\text{Fitting}) + \text{Error}(\text{Matching})$$



---

## ✨ Key Features

* **Active Perception Loop:** Implements an iterative bootstrapping process where the mental world is used as a cue to search for clues in reality.
* **MTSF Extraction:** Generates *Minimal Transparent Semantic Features* including:
    * **COLOR:** CIELab-based robust Qualia classification.
    * **BBOX:** Law of Praegnanz-driven bounding box simplification.
    * **SHAPE/SIZE:** Spatial distribution and pixel-wise density analysis.
* **Recursive Clustering:** Dynamically adjusts parameters ($\beta$) to resolve individual objects within detected groups (Law of Similarity).
* **Transparent State Updates:** Actively adjusts the 6D-pose of objects in the mental world to minimize matching error.

---

## 🛠 Project Structure

The package is organized to separate cognitive logic from low-level vision kernels:

* `src/gestalt/core.py`: The recursive engine implementing Algorithm 1.
* `src/gestalt/mtsf.py`: Semantic feature extraction (Qualia, Shape, Size).
* `src/gestalt/matching.py`: Law of Closure logic and weighted vector distance.
* `src/gestalt/vision_utils.py`: Refined BGR-to-CIELab and Gaussian denoising filters.



---

## 🚀 Quick Start

### Installation
```bash
git clone [https://github.com/fkenghagho/gestalt_perception.git](https://github.com/fkenghagho/gestalt_perception.git)
cd gestalt_perception
pip install -e .
```

### Execution

```python
"""
Gestalt Perception Engine
Core implementation of the Gestalt Distance Algorithm.

Author: Franklin Kenghagho Kenfack
Reference: https://media.suub.uni-bremen.de/handle/elib/23082 (PhD Dissertation, 2025)
"""

from gestalt.core import GestaltEngine
from gestalt.mtsf import MTSFExtractor

# 1. Define Weights for Minimal Transparent Semantic Features (MTSFs)
# Order: [Color, Size, Shape, BBox]
lambdas = (0.4, 0.1, 0.2, 0.3)

# 2. Initialize Engine 
# delta: penalty for unfitted stimuli (expressiveness of the mental theory)
engine = GestaltEngine(lambdas=lambdas, delta=1.5, extractor=MTSFExtractor())

# 3. Compute Distance between Observation (Z) and Mental Particle (X)
# beta: parameters for edge-detection based object clustering
distance = engine.compute(
    observation=camera_frame, 
    mental_particle=current_theory_particle, 
    beta={'T_lower': 50, 'T_upper': 150}
)

print(f"Computed Gestalt Distance: {distance}")
```
