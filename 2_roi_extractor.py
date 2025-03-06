import os
import json
import argparse
from PIL import Image

# Set the OpenSlide DLL directory for Windows
OPENSLIDE_PATH = r'./software/openslide-bin-4.0.0.6-windows-x64/openslide-bin-4.0.0.6-windows-x64/bin'
if hasattr(os, 'add_dll_directory'):
    with os.add_dll_directory(OPENSLIDE_PATH):
        import openslide
else:
    import openslide


def load_annotations(json_file):
    """
    Load annotations from a JSON file.

    Args:
        json_file (str): Path to the JSON file containing annotations.

    Returns:
        list: A list of annotation dictionaries loaded from the file.

    Author: Ling Luo
    Date: 2025-03-06
    """
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


def is_blue(color_int):
    """
    Check if the provided color (as an integer) is predominantly blue.

    The color is assumed to be in ARGB format. This function extracts each channel and
    returns True if the blue channel is higher than the red and green channels and is above 128.

    Args:
        color_int (int): The integer representing the ARGB color.

    Returns:
        bool: True if the color is considered blue, False otherwise.

    Author: Ling Luo
    Date: 2025-03-06
    """
    alpha = (color_int >> 24) & 0xff
    red   = (color_int >> 16) & 0xff
    green = (color_int >> 8)  & 0xff
    blue  = color_int & 0xff

    return blue > red and blue > green and blue > 128


def find_blue_rois(annotations):
    """
    Find and return all regions of interest (ROIs) in the annotations that are blue.

    It iterates over each annotation and uses the is_blue() function to test the color.

    Args:
        annotations (list): List of annotation dictionaries.

    Returns:
        list: A list of dictionaries, each with keys 'x', 'y', 'width', and 'height' for a blue ROI.
              Returns an empty list if no blue ROIs are found.

    Author: Ling Luo
    Date: 2025-03-06
    """
    blue_rois = []
    for item in annotations:
        if is_blue(item['color']):
            region = item['region']
            blue_rois.append({
                'x': int(region['x']),
                'y': int(region['y']),
                'width': int(region['width']),
                'height': int(region['height'])
            })
    return blue_rois


def adjust_roi(roi):
    """
    Adjust the ROI coordinates based on the sign of width and height.

    According to the rules:
      - If width and height are both positive, no change is needed.
      - If width > 0 and height < 0, the starting point is bottom-right;
        subtract the width from x.
      - If width and height are both negative, the starting point is top-right;
        subtract the absolute width from x.
      - If width < 0 and height > 0 (if it occurs), assume the given coordinates are correct.

    The width and height are converted to positive values.

    Args:
        roi (dict): A dictionary with keys 'x', 'y', 'width', and 'height'.

    Returns:
        dict: Adjusted ROI with keys 'x', 'y', 'width', and 'height'.

    Author: Ling Luo
    Date: 2025-03-06
    """
    x = roi['x']
    y = roi['y']
    w = roi['width']
    h = roi['height']

    if w > 0 and h > 0:
        new_x = x
        new_y = y
    elif w < 0 and h > 0:
        new_x = x + w
        new_y = y
    elif w > 0 and h < 0:
        new_x = x
        new_y = y + h
    elif w < 0 and h < 0:
        new_x = x + w
        new_y = y + h

    return {
        'x': new_x,
        'y': new_y,
        'width': abs(w),
        'height': abs(h)
    }


def crop_region(svs_path, roi, level=0):
    """
    Crop a region from an SVS image and return it as a PIL Image in RGB format.

    The ROI is first adjusted based on the sign of width and height so that it
    correctly represents the top-left coordinate and positive dimensions.

    Args:
        svs_path (str): Path to the SVS image file.
        roi (dict): Dictionary with keys 'x', 'y', 'width', 'height' defining the crop area.
        level (int): The resolution level to use (0 is the highest resolution).

    Returns:
        PIL.Image: The cropped region as a PIL Image in RGB format.

    Author: Ling Luo
    Date: 2025-03-06
    """
    slide = openslide.OpenSlide(svs_path)
    adjusted_roi = adjust_roi(roi)
    region = slide.read_region((adjusted_roi['x'], adjusted_roi['y']), level,
                               (adjusted_roi['width'], adjusted_roi['height']))
    region = region.convert("RGB")
    return region


def save_region(image, output_path, fmt):
    """
    Save a PIL Image to a file with the specified format.

    Args:
        image (PIL.Image): The image to save.
        output_path (str): The path where the image will be saved.
        fmt (str): The image format to use (e.g., "PNG", "TIFF").

    Author: Ling Luo
    Date: 2025-03-06
    """
    image.save(output_path, format=fmt)
    print(f"Saved image as {output_path}")


def main(json_file, svs_path, out_path):
    """
    Main function that orchestrates the process:
    1. Loads the annotation data from a JSON file.
    2. Finds all blue regions of interest (ROIs).
    3. Crops each ROI from the SVS image.
    4. Saves each cropped region in both SVS (TIFF) and PNG formats in specified output directories.

    The output files are named using the base name of the SVS file followed by "-roi{idx}".
    The files are saved in out_path\svs\ and out_path\png\ respectively.

    Args:
        json_file (str): Path to the JSON file containing annotations.
        svs_path (str): Path to the SVS image file.
        out_path (str): Base output directory to save the cropped images.

    Author: Ling Luo
    Date: 2025-03-06
    """
    svs_output_dir = os.path.join(out_path, "svs")
    png_output_dir = os.path.join(out_path, "png")
    os.makedirs(svs_output_dir, exist_ok=True)
    os.makedirs(png_output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(svs_path))[0]
    annotations = load_annotations(json_file)
    blue_rois = find_blue_rois(annotations)
    print("Detected blue ROIs:", blue_rois)
    if not blue_rois:
        print("No blue regions found in the annotations.")
        return

    for idx, roi in enumerate(blue_rois, start=1):
        png_file = os.path.join(png_output_dir, f"{base_name}-roi{idx}.png")
        svs_file = os.path.join(svs_output_dir, f"{base_name}-roi{idx}.svs")

        cropped_image = crop_region(svs_path, roi)
        save_region(cropped_image, png_file, fmt="PNG")
        save_region(cropped_image, svs_file, fmt="TIFF")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Crop blue regions from an SVS image using annotation data from a JSON file."
    )
    parser.add_argument(
        "--json_file",
        type=str,
        default=r'./Annotations/1.json',
        help="Path to the JSON annotation file."
    )
    parser.add_argument(
        "--svs_path",
        type=str,
        default=r'./svs/1.svs',
        help="Path to the SVS image file."
    )
    parser.add_argument(
        "--out_path",
        type=str,
        default=r'./data_example/output',
        help="Base output directory to save the cropped images."
    )

    args = parser.parse_args()
    main(json_file=args.json_file, svs_path=args.svs_path, out_path=args.out_path)
