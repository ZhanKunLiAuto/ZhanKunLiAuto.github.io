---
layout: page
title: Street Gaussians
description: Modeling dynamic urban scenes with Gaussian splatting for autonomous driving
img: assets/img/publication_preview/street_gaussians.png
importance: 2
category: work
giscus_comments: true
---

# Street Gaussians: Next-Generation Urban Scene Modeling

## Project Overview

Street Gaussians introduces a revolutionary approach to modeling dynamic urban environments using 3D Gaussian Splatting. This project enables high-fidelity reconstruction and real-time rendering of complex urban scenes, supporting advanced autonomous driving simulation and scene understanding applications.

<div class="row">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/publication_preview/street_gaussians.png" title="Street Gaussians Rendering" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    High-fidelity rendering of dynamic urban scenes using Street Gaussians.
</div>

## Technical Innovation

### 🌆 Dynamic Scene Modeling
- **Real-time Rendering**: Photorealistic rendering of complex urban environments at 60+ FPS
- **Dynamic Objects**: Accurate representation of moving vehicles, pedestrians, and environmental changes
- **Multi-scale Representation**: Efficient handling of both large-scale city layouts and fine details

### 🎯 Key Features
- **High Fidelity**: Near-photorealistic quality with minimal artifacts
- **Temporal Consistency**: Smooth temporal transitions for video generation
- **Scalability**: Efficient memory usage for large-scale urban environments
- **Real-time Performance**: Optimized for autonomous driving simulation requirements

## Applications in Autonomous Driving

### 🚗 Simulation & Training
- **Scenario Generation**: Create diverse driving scenarios for training and testing
- **Data Augmentation**: Generate synthetic training data with controlled variations
- **Edge Case Simulation**: Model rare but critical driving situations

### 🔍 Scene Understanding
- **3D Reconstruction**: Accurate 3D models of real-world driving environments
- **Temporal Analysis**: Understanding of dynamic scene evolution over time
- **Predictive Modeling**: Anticipating future scene states for planning

## Research Impact

**102 Citations** and acceptance at **ECCV 2024** demonstrate the significant impact of this work on the computer vision and autonomous driving communities. The project has established new standards for urban scene modeling and has been adopted by numerous research groups worldwide.

## Technical Specifications

- **Framework**: PyTorch-based implementation with CUDA optimization
- **Performance**: Real-time rendering on consumer GPUs
- **Dataset Compatibility**: Support for multiple autonomous driving datasets
- **Integration**: Seamless integration with existing simulation pipelines

<div class="row">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/2.jpg" title="Technical Pipeline" class="img-fluid rounded z-depth-1" %}
    </div>
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/3.jpg" title="Results Comparison" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    Left: Technical pipeline of Street Gaussians. Right: Comparison with traditional rendering methods.
</div>

This project represents a significant advancement in 3D scene representation for autonomous driving, providing the foundation for more realistic simulation environments and enhanced scene understanding capabilities.
