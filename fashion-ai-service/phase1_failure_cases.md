# Phase 1: Clothing Intelligence Pipeline Failure Cases & Mitigations

Digitizing real-world wardrobes is highly susceptible to messy user inputs (bad lighting, cluttered backgrounds, folded clothes). This document logs the primary failure modes of our AI pipeline and details programmatic mitigations.

---

## 1. Background Removal Failures (rembg / U2-Net)

### Failure Mode 1.1: Contrast Boundary Blending
*   **Description:** When a garment color closely matches the background color (e.g., a white t-shirt on white bedsheets, or a black blazer on a dark leather chair), `rembg` U2-Net fails to detect edges, resulting in parts of the garment being cropped out or chunks of the bedsheet being preserved.
*   **Visual Outcome:** "Holes" inside the garment or jagged bedsheet outlines remaining in the processed PNG.
*   **Programmatic Mitigation:**
    *   *Short-term:* Prompt the user in the UI with a "Contrast Alert" if the boundary pixel delta is too low.
    *   *Long-term:* Integrate Meta's **Segment Anything Model (SAM)** or **YOLOv8-pose** to run a secondary pass with localized bounding boxes.

### Failure Mode 1.2: Hanger and Hand Inclusions
*   **Description:** Mirror selfies where the user holds the phone or clothing hung on wooden/plastic hangers. The background removal algorithm preserves the hanger or the user's arm/fingers because they are touching the garment.
*   **Visual Outcome:** A clean cropped shirt, but with floating disembodied fingers or a hanger sticking out of the collar.
*   **Programmatic Mitigation:**
    *   Utilize an object detection model (e.g., fine-tuned YOLO) to detect standard "Hanger" and "Human Hand" bounding boxes and mask them out before running classification.

---

## 2. Image Preprocessing & Cropping Failures

### Failure Mode 2.1: Aspect Ratio Distortions
*   **Description:** Scaling tall boots or wide jackets directly to 512x512 without aspect ratio protection squashes wide coats or stretches narrow trousers.
*   **Visual Outcome:** Squished, distorted garments that alter the visual style and confuse the CLIP embedding generator.
*   **Programmatic Mitigation:**
    *   *Implemented:* Our `ImagePreprocessor` enforces a strict 1:1 padding rule. It wraps the cropped bounding box of the garment in a transparent square container *before* resizing, guaranteeing that native proportions are preserved.

---

## 3. Color Extraction Engine Failures (OpenCV LAB KMeans)

### Failure Mode 3.1: Contrast/Shadow Color Shifts
*   **Description:** Clothes photographed in low light or harsh shadow cast. The KMeans color extractor identifies dark grey or brown as the primary color instead of the actual garment tone (e.g., beige looks brown under shadows).
*   **Visual Outcome:** Primary color classified as "black" or "grey" instead of its true vibrant hue.
*   **Programmatic Mitigation:**
    *   Prior to color clustering, perform **CLAHE (Contrast Limited Adaptive Histogram Equalization)** in the L\*a\*b\* light channel to balance shadows and exposure dynamically.

### Failure Mode 3.2: Multi-color Pattern Dilation
*   **Description:** Striped shirts, checkered patterns, or floral dresses. The KMeans clusters yield intermediate "muddy" colors formed by averaging pixel transitions at pattern boundaries.
*   **Visual Outcome:** A black-and-white striped shirt yields a dominant color classified as "grey" because it averages the alternating stripes.
*   **Programmatic Mitigation:**
    *   Calculate saturation and color variance. If variance is high, rely on the Gemini multimodal classification model's pattern identification (`extracted_metadata.pattern` like "striped" or "checkered") to override color heuristics and return both distinct primary/secondary colors.

---

## 4. Metadata Classification Failures (Gemini Multimodal)

### Failure Mode 4.1: Folded/Lying Garment Classification
*   **Description:** Flat-lay photos where clothes are folded or heavily wrinkled on the floor. The LLM cannot see the silhouette, sleeves, or hem length.
*   **Visual Outcome:** An oversized t-shirt misclassified as a "slim-fit polo" or a maxi dress classified as a "skirt".
*   **Programmatic Mitigation:**
    *   Provide explicit photographic guidelines in the mobile onboarding UI (e.g., "hang or flat-lay garments completely flat").
    *   Expose a simple UI card in the app allowing users to edit and override extracted attributes (e.g., changing "slim" to "oversized") which then triggers an attributes correction event to fine-tune future recommendations.
