# Slide2Patch 🔬🖼️

**Slide2Patch** is an open-source toolkit designed for beginners in digital pathology. It converts KFB slides to the widely used SVS format, extracts Regions of Interest (ROIs) using annotation data, and subdivides them into smaller patches for detailed analysis.

---

## Overview 🚀

Digital pathology often requires processing large, high-resolution slides. **Slide2Patch** simplifies this process by:
- Converting proprietary KFB slides to the standard SVS format.
- Segmenting SVS images based on annotation data to extract precise ROIs.
- Dividing each ROI into smaller patches suitable for machine learning, diagnostics, or further image analysis.

Whether you're a researcher, clinician, or developer, Slide2Patch streamlines your workflow from raw slide data to actionable image patches.

---

## Features 🔧

- **KFB to SVS Conversion**  
  Convert high-resolution KFB slides to the widely-used SVS format with ease.

- **ROI Extraction**  
  Automatically segment SVS images using provided annotations to extract Regions of Interest.

- **Patch Generation**  
  Further divide extracted ROIs into smaller patches for scalable analysis.

---

## Installation 📦

1. **Download and Setup KFB Conversion Tool:**
   - Visit [kfb2svs Releases](https://github.com/tcmyxc/kfb2svs/releases) and download the latest kfb2svs package.
   - Extract the downloaded package. The `kfb2svs_converter.py` script requires the included `KFbioConverter.exe` tool.

2. **Install OpenSlide:**
   - Download the appropriate OpenSlide binary from [OpenSlide Downloads](https://openslide.org/download/).
   - Install the Python bindings by running:
     ```bash
     pip install openslide-python
     ```

