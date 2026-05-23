import logging
import numpy as np
import cv2
from PIL import Image
from sklearn.cluster import KMeans

logger = logging.getLogger("fashion-ai-service")

# A curated catalog of standard fashion colors and their coordinates in CIE L*a*b* space.
# Coordinates are pre-computed using OpenCV: cv2.cvtColor(np.uint8([[[R, G, B]]]), cv2.COLOR_RGB2Lab)
STANDARD_FASHION_COLORS = {
    "white":   {"hex": "#FFFFFF", "lab": np.array([255, 128, 128])}, # Standard normalized LAB in OpenCV uint8 range
    "black":   {"hex": "#000000", "lab": np.array([0, 128, 128])},
    "grey":    {"hex": "#808080", "lab": np.array([137, 128, 128])},
    "beige":   {"hex": "#F5F5DC", "lab": np.array([243, 121, 137])},
    "cream":   {"hex": "#FFFDD0", "lab": np.array([251, 122, 139])},
    "navy":    {"hex": "#000080", "lab": np.array([33, 149, 73])},
    "blue":    {"hex": "#0000FF", "lab": np.array([82, 179, 58])},
    "light_blue": {"hex": "#ADD8E6", "lab": np.array([215, 118, 107])},
    "olive":   {"hex": "#808000", "lab": np.array([136, 110, 158])},
    "green":   {"hex": "#008000", "lab": np.array([120, 78, 168])},
    "red":     {"hex": "#FF0000", "lab": np.array([135, 204, 172])},
    "maroon":  {"hex": "#800000", "lab": np.array([68, 166, 150])},
    "pink":    {"hex": "#FFC0CB", "lab": np.array([216, 144, 132])},
    "orange":  {"hex": "#FFA500", "lab": np.array([182, 157, 182])},
    "yellow":  {"hex": "#FFFF00", "lab": np.array([245, 106, 202])},
    "purple":  {"hex": "#800080", "lab": np.array([79, 179, 93])},
    "brown":   {"hex": "#A52A2A", "lab": np.array([96, 160, 151])}
}

class ColorExtractor:
    @staticmethod
    def rgb_to_lab(rgb_array: np.ndarray) -> np.ndarray:
        """Converts an N x 3 array of RGB pixels into CIE L*a*b* pixels."""
        # Reshape to 3D image-like array (N, 1, 3) for OpenCV compatibility
        pixel_img = rgb_array.astype(np.uint8).reshape(-1, 1, 3)
        lab_img = cv2.cvtColor(pixel_img, cv2.COLOR_RGB2Lab)
        return lab_img.reshape(-1, 3)

    @staticmethod
    def lab_to_hex(lab_centroid: np.ndarray) -> str:
        """Converts a single L*a*b* OpenCV centroid back to an RGB Hex string."""
        # Reshape to (1, 1, 3) 3D image-like array for OpenCV
        lab_pixel = lab_centroid.astype(np.uint8).reshape(1, 1, 3)
        rgb_pixel = cv2.cvtColor(lab_pixel, cv2.COLOR_Lab2RGB)
        r, g, b = rgb_pixel[0, 0]
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def map_lab_to_fashion_color(lab_centroid: np.ndarray) -> str:
        """Calculates Delta-E (Euclidean in LAB) to map centroids to fashion labels."""
        closest_color = "unknown"
        min_distance = float("inf")
        
        for name, data in STANDARD_FASHION_COLORS.items():
            # Delta-E 76: Simple Euclidean distance in LAB coordinates
            distance = np.linalg.norm(lab_centroid - data["lab"])
            if distance < min_distance:
                min_distance = distance
                closest_color = name
                
        return closest_color

    @staticmethod
    def extract_colors(pil_image: Image.Image) -> tuple[str, list[str], str, list[str]]:
        """
        Filters out transparent pixels, clusters remaining pixels using KMeans, 
        and extracts primary and secondary fashion colors along with their exact Hex codes.
        Returns: (primary_color_name, [secondary_color_names], primary_hex, [secondary_hexes])
        """
        try:
            # 1. Inspect image and load RGBA pixel channels
            img_rgba = pil_image.convert("RGBA")
            pixels = np.array(img_rgba)
            
            # Reshape pixels to (Width * Height, 4)
            pixels_flat = pixels.reshape(-1, 4)
            
            # 2. Alpha Channel Masking: Filter out transparent/semi-transparent pixels (Alpha < 50)
            non_transparent_mask = pixels_flat[:, 3] >= 50
            rgb_pixels = pixels_flat[non_transparent_mask, :3]
            
            # If the image is completely transparent or lacks valid pixels, default
            if rgb_pixels.shape[0] < 100:
                logger.warning("Fewer than 100 non-transparent pixels found. Defaulting to white/no secondary.")
                return "white", [], "#ffffff", []

            # 3. Convert active garment pixels to CIE L*a*b* space
            lab_pixels = ColorExtractor.rgb_to_lab(rgb_pixels)
            
            # 4. Perform KMeans Clustering
            # k=3 clusters represent Primary, Secondary, and Accent tones
            n_clusters = min(3, lab_pixels.shape[0])
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            kmeans.fit(lab_pixels)
            
            centroids = kmeans.cluster_centers_
            labels = kmeans.labels_
            
            # Count pixels belonging to each cluster to estimate proportions
            counts = np.bincount(labels)
            total_pixels = len(labels)
            
            # Sort clusters by pixel volume (descending)
            sorted_indices = np.argsort(counts)[::-1]
            
            # 5. Extract colors using Delta-E mapping and Hex conversions
            extracted_colors = []
            for idx in sorted_indices:
                proportion = counts[idx] / total_pixels
                # Convert LAB centroid to clean fashion string name
                color_name = ColorExtractor.map_lab_to_fashion_color(centroids[idx])
                # Convert LAB centroid to precise hex string
                hex_code = ColorExtractor.lab_to_hex(centroids[idx])
                
                # Check for duplicate names (e.g. if centroid 1 and centroid 2 both map to 'navy')
                if color_name not in [c[0] for c in extracted_colors]:
                    extracted_colors.append((color_name, hex_code, proportion))
            
            # Primary color is the highest-volume cluster
            primary_color = extracted_colors[0][0]
            primary_hex = extracted_colors[0][1]
            
            # Secondary colors are clusters exceeding 15% of the garment surface area
            secondary_colors = []
            secondary_hexes = []
            for name, hex_code, prop in extracted_colors[1:]:
                if prop >= 0.15:
                    secondary_colors.append(name)
                    secondary_hexes.append(hex_code)
                    
            logger.info(
                f"Color extraction complete. Primary: '{primary_color}' ({primary_hex}), "
                f"Secondaries: {secondary_colors} ({secondary_hexes})"
            )
            
            return primary_color, secondary_colors, primary_hex, secondary_hexes
            
        except Exception as e:
            logger.error(f"Error in color extraction: {str(e)}")
            return "white", [], "#ffffff", []
