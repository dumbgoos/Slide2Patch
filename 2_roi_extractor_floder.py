import os
import json
import argparse
from PIL import Image

# Set the OpenSlide DLL directory for Windows
OPENSLIDE_PATH = r'D:\\software\\openslide-bin-4.0.0.6-windows-x64\\openslide-bin-4.0.0.6-windows-x64\\bin'
if hasattr(os, 'add_dll_directory'):
    with os.add_dll_directory(OPENSLIDE_PATH):
        import openslide
else:
    import openslide


def load_annotations(json_file):
    """
    Load annotation data from a JSON file.

    Args:
        json_file (str): The path to the JSON file.

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
    Determine if the given color (represented as an integer) is primarily blue.

    The color is in ARGB format. This function extracts each channel and considers the color blue if 
    the blue channel value is greater than both the red and green channels and is greater than 128.

    Args:
        color_int (int): An integer representing an ARGB color.

    Returns:
        bool: True if the color is considered blue, otherwise False.

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
    Find and return all blue regions of interest (ROIs).

    Iterates over all annotations and uses the is_blue() function to determine the color.

    Args:
        annotations (list): A list of annotation dictionaries.

    Returns:
        list: A list where each element is a blue ROI dictionary containing 'x', 'y', 'width', and 'height' keys.
              Returns an empty list if no blue ROI is found.

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
    Adjust the ROI coordinates based on the signs of width and height.

    Rules:
      - If both width and height are positive, no adjustment is needed.
      - If width > 0 and height < 0, the starting point is the bottom-right; adjust the y-coordinate by adding the negative height.
      - If both width and height are negative, the starting point is the bottom-right.
      - If width < 0 and height > 0, the starting point is the top-left; only take the absolute value of the width.

    Args:
        roi (dict): A dictionary containing 'x', 'y', 'width', and 'height' keys.

    Returns:
        dict: The adjusted ROI with positive 'width' and 'height' values.

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
    Crop the specified ROI region from an SVS image and return a PIL image in RGB format.

    First, adjust the ROI coordinates based on the width and height, then read the region from the corresponding resolution level.

    Args:
        svs_path (str): The path to the SVS image file.
        roi (dict): A dictionary defining the cropping region with 'x', 'y', 'width', and 'height' keys.
        level (int): The resolution level to use (0 for the highest resolution).

    Returns:
        PIL.Image: The cropped image in RGB format.

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
    Save a PIL image as a file in the specified format.

    Args:
        image (PIL.Image): The image to be saved.
        output_path (str): The path where the image will be saved.
        fmt (str): The image format (e.g., "PNG", "TIFF").

    Author: Ling Luo
    Date: 2025-03-06
    """
    image.save(output_path, format=fmt)
    print(f"Saved image as {output_path}")


def process_folder(json_folder, svs_folder, out_path, level=0):
    """
    Batch process all images in the SVS folder and extract blue ROIs based on the corresponding JSON annotations.

    For each .svs file in svs_folder:
      - Obtain the file name (without the extension) and convert it to lowercase.
      - Look for the corresponding subfolder in json_folder (named with the lowercase file name) containing the "1.json" file.
      - If found, load the annotations, filter blue ROIs, crop the image for each ROI, and save the results in the 'svs' and 'png' folders under out_path.

    Args:
        json_folder (str): The root directory that stores JSON annotation subfolders. Each subfolder should be named after the corresponding SVS file (in lowercase) and contain a "1.json" file.
        svs_folder (str): The folder containing SVS image files.
        out_path (str): The root directory for the output cropped images.
        level (int): The resolution level to use when cropping (default is 0).

    Author: Ling Luo
    Date: 2025-03-06
    """
    svs_output_dir = os.path.join(out_path, "svs")
    png_output_dir = os.path.join(out_path, "png")
    os.makedirs(svs_output_dir, exist_ok=True)
    os.makedirs(png_output_dir, exist_ok=True)

    # Iterate over all .svs files in svs_folder
    for filename in os.listdir(svs_folder):
        if filename.lower().endswith('.svs'):
            svs_path = os.path.join(svs_folder, filename)
            base_name = os.path.splitext(filename)[0].lower()  # Convert to lowercase
            # Expected JSON file at json_folder/base_name_kfb/Annotations/1.json
            json_file = os.path.join(json_folder, f'{base_name}_kfb', 'Annotations', "1.json")
            if not os.path.exists(json_file):
                print(f"JSON file corresponding to {filename} not found, expected path: {json_file}")
                continue

            annotations = load_annotations(json_file)
            blue_rois = find_blue_rois(annotations)
            print(f"Processing {filename}, detected blue ROIs:", blue_rois)
            if not blue_rois:
                print(f"No blue regions found in the annotations for {filename}.")
                continue

            for idx, roi in enumerate(blue_rois, start=1):
                png_file = os.path.join(png_output_dir, f"{base_name}-roi{idx}.png")
                svs_file_out = os.path.join(svs_output_dir, f"{base_name}-roi{idx}.svs")
                cropped_image = crop_region(svs_path, roi, level=level)
                save_region(cropped_image, png_file, fmt="PNG")
                save_region(cropped_image, svs_file_out, fmt="TIFF")


def main(json_folder, svs_folder, out_path):
    """
    Main function: Call process_folder to handle folders containing JSON and SVS files.

    Args:
        json_folder (str): The root directory that stores JSON annotation subfolders.
        svs_folder (str): The folder containing SVS image files.
        out_path (str): The root directory for the output cropped images.

    Author: Ling Luo
    Date: 2025-03-06
    """
    process_folder(json_folder, svs_folder, out_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Crop blue regions from SVS images based on JSON annotations stored in folders."
    )
    parser.add_argument(
        "--json_folder",
        type=str,
        default=r'D:\\my work\\GC-IMC\\data\\trainSvs\\',
        help="Root directory for JSON annotation subfolders. Each subfolder (in lowercase) corresponds to an SVS file and should contain a '1.json' file."
    )
    parser.add_argument(
        "--svs_folder",
        type=str,
        default=r'D:\\my work\\GC-IMC\\data\\trainConvertToSvs\\',
        help="Folder containing SVS image files."
    )
    parser.add_argument(
        "--out_path",
        type=str,
        default=r'D:\\my work\\GC-IMC\\data\\train_roi',
        help="Output root directory for the cropped images."
    )

    args = parser.parse_args()
    main(json_folder=args.json_folder, svs_folder=args.svs_folder, out_path=args.out_path)
