import numpy as np
import skimage as sk
from pydicom import FileDataset
from pydicom.pixels import pixel_array
from skimage.measure._regionprops import RegionProperties
from skimage.morphology import convex_hull_image

# Parameters
ALPHA: float = 0.98
BETA: float = 45.0
GAMMA: float = 1.0 / 3.0
DELTA: float = 1.0 / 100.0
MAX_THRESHOLD_ITER: int = 50
ACM_MAX_ITER: int = 150
TARGET_SIZE: int = 1024


def check_individual_assessment(
    lung: RegionProperties, image_shape: tuple[int, int]
) -> int:
    """Compute the number of failure of individual assessments

    Args:
        lung (RegionProperties): RegionProperties of a lung (left or right)
        image_shape (tuple[int, int]): Shape of the original image

    Returns:
        int: Number of failure of individual assessments
    """
    number_failure_individual_assessment: int = 0
    image_height, image_width = image_shape
    image_area: int = image_height * image_width

    # Check Eccentricity
    if lung.eccentricity <= ALPHA:
        number_failure_individual_assessment += 1

    # Check Equivalent Diameter
    if lung.equivalent_diameter_area <= BETA:
        number_failure_individual_assessment += 1

    # Check Filled Area
    filled_area_ratio: float = lung.area_filled / image_area
    if filled_area_ratio > GAMMA:
        number_failure_individual_assessment += 1

    if filled_area_ratio < DELTA:
        number_failure_individual_assessment += 1

    # Check ROI is adjacent to image borders
    # min_row, min_col, max_row, max_col = lung.bbox
    # if (
    #     min_row == 0
    #     or min_col == 0
    #     or max_row == image_height
    #     or max_col == image_width
    # ):
    #     print("Adjacent")
    #     number_failure_individual_assessment += 1

    return number_failure_individual_assessment


def check_similarity_assessment(
    left_lung: RegionProperties,
    right_lung: RegionProperties,
    left_right_lung_mask: np.ndarray,
    image_area: int,
) -> int:
    """Compute the number of failure of similarity assessments

    Args:
        left_lung (RegionProperties): RegionProperties of the left lung
        right_lung (RegionProperties): RegionProperties of the right lung
        left_right_lung_mask (np.ndarray): Mask with both left and right lungs
        image_area (int): Area of the original image

    Returns:
        int: Number of failure of similarity assessments
    """
    number_failure_similarity_assessment: int = 0

    # Check Major Axis Length
    axis_major_length_left_lung: float = left_lung.axis_major_length
    axis_major_length_right_lung: float = right_lung.axis_major_length

    if (axis_major_length_left_lung > 1.5 * axis_major_length_right_lung) or (
        axis_major_length_right_lung > 1.5 * axis_major_length_left_lung
    ):
        number_failure_similarity_assessment += 1

    # Check Convex Area

    # left_right_lung_prop: RegionProperties = sk.measure.regionprops(
    #     left_right_lung_mask.astype(int)
    # )[0]
    # if left_right_lung_prop.area_convex > (image_area / 3.0):
    #     number_failure_similarity_assessment += 1

    return number_failure_similarity_assessment


def recursive_thresholding(
    denoised_image_arr: np.ndarray, theta_0: float
) -> tuple[np.ndarray, np.ndarray]:
    """Binarization with Recursive Thresholding and Lung Field Identification

    Args:
        denoised_image_arr (np.ndarray): Denoised original image
        theta_0 (float): Global threshold computed with ISODATA

    Returns:
        tuple[np.ndarray, np.ndarray]: Convex hulls as binary masks for each lung
    """
    for i in range(MAX_THRESHOLD_ITER):
        # Perform global binarization denoised image at threshold theta_0
        binarized_image_arr: np.ndarray = denoised_image_arr <= theta_0

        # Get all the connected components
        labels, num = sk.measure.label(binarized_image_arr, return_num=True)
        print(f"Number of connected components detected: {num}")

        # Compute image area
        image_area: int = binarized_image_arr.shape[0] * binarized_image_arr.shape[1]

        # Exclude artifacts (too small or too big)
        props: list[RegionProperties] = [
            prop
            for prop in sk.measure.regionprops(labels)
            if not (prop.area > image_area / 4 or prop.area < image_area / 100)
        ]

        print(
            f"Number of connected components detected after excluding artifacts: {len(props)}"
        )

        """
        Identify leftLung as the connected component with minimal Euclidean distance from its centroid to the upper left half of the image.
        Identify rightLung as the connected component with minimal Euclidean distance from its centroid to the upper right half of the image
        """
        left_lung: RegionProperties | None = None
        left_lung_dist: float = 0.0
        right_lung: RegionProperties | None = None
        right_lung_dist: float = 0.0

        # Iterate over each connected components to identify left and right lungs
        for prop in props:
            # Compute centroid point with (x,y) order
            centroid: np.ndarray = np.array([prop.centroid[1], prop.centroid[0]])

            # Compute the euclidean distance from its centroid to the upper left half of the image (middle point)
            euclidean_distance_from_centroid_to_upper_left_half_of_image: float = float(
                np.linalg.norm(
                    centroid
                    - np.array(
                        [
                            binarized_image_arr.shape[1] // 2.5,
                            binarized_image_arr.shape[0] // 2,
                        ]
                    )
                )
            )

            # Compute the euclidean distance from its centroid to the upper right half of the image (middle point)
            euclidean_distance_from_centroid_to_upper_right_half_of_image: float = (
                float(
                    np.linalg.norm(
                        centroid
                        - np.array(
                            [
                                3 * binarized_image_arr.shape[1] // 5.0,
                                binarized_image_arr.shape[0] // 2,
                            ]
                        )
                    )
                )
            )

            # Verify if the computed distances are smaller than the stored distances
            if (
                left_lung is not None
                and euclidean_distance_from_centroid_to_upper_left_half_of_image
                < left_lung_dist
            ) or left_lung is None:
                left_lung = prop
                left_lung_dist = (
                    euclidean_distance_from_centroid_to_upper_left_half_of_image
                )

            if (
                right_lung is not None
                and euclidean_distance_from_centroid_to_upper_right_half_of_image
                < right_lung_dist
            ) or right_lung is None:
                right_lung = prop
                right_lung_dist = (
                    euclidean_distance_from_centroid_to_upper_right_half_of_image
                )

        # Sanity check
        if left_lung is not None and right_lung is not None:
            # Case where we have the same component for both lung
            if left_lung.label == right_lung.label:
                theta_0 *= 0.95
                continue
            # Check for individual assessment for left and right lungs
            number_failure_individual_assessment: int = check_individual_assessment(
                left_lung, binarized_image_arr.shape
            ) + check_individual_assessment(right_lung, binarized_image_arr.shape)

            # Merge the two lung masks
            left_right_lung_mask: np.ndarray = np.isin(
                labels, [left_lung.label, right_lung.label]
            )

            # Check for similarity assessment
            number_failure_similarity_assessment: int = check_similarity_assessment(
                left_lung, right_lung, left_right_lung_mask, image_area
            )

            # Check that quality of segmentation is satisfactory
            if (
                number_failure_individual_assessment >= 2
                and number_failure_similarity_assessment >= 1
            ):
                theta_0 = theta_0 * 0.95
            else:
                # Generate convex hulls from left lung and right lung
                left_lung_mask: np.ndarray = labels == left_lung.label
                right_lung_mask: np.ndarray = labels == right_lung.label
                left_lung_convex_hull_mask: np.ndarray = convex_hull_image(
                    left_lung_mask
                )
                right_lung_convex_hull_mask: np.ndarray = convex_hull_image(
                    right_lung_mask
                )
                return left_lung_convex_hull_mask, right_lung_convex_hull_mask
        else:
            theta_0 = theta_0 * 0.95
    # Sanity return
    return (
        np.zeros_like(denoised_image_arr, dtype=bool),
        np.zeros_like(denoised_image_arr, dtype=bool),
    )


def apply_stacked_active_contour(
    convex_hull_quadrant: np.ndarray, denoised_image_arr: np.ndarray
) -> np.ndarray:
    """Apply the active contour model on a mask

    Args:
        convex_hull_quadrant (np.ndarray): Mask of a quadrant of the convex hull
        denoised_image_arr (np.ndarray): Denoised original image

    Returns:
        np.ndarray: Mask of a quadrant of the convex hull with active contour model applied
    """
    # Find the contours of the convex hull mask
    contours: list[np.ndarray] = sk.measure.find_contours(
        convex_hull_quadrant.astype(float)
    )

    # Sanity check
    if not contours:
        return convex_hull_quadrant

    # Get the largest contour (so the one corresponding to the lung)
    init_snake: np.ndarray = max(contours, key=len)

    # Apply the active contour model
    snake: np.ndarray = sk.segmentation.active_contour(
        image=denoised_image_arr,
        snake=init_snake,
        max_num_iter=ACM_MAX_ITER,
        beta=0.001,
    )

    # Create a mask with the result of the active contour model
    mask: np.ndarray = np.zeros(convex_hull_quadrant.shape, dtype=bool)
    rr, cc = sk.draw.polygon(snake[:, 0], snake[:, 1], shape=mask.shape)
    mask[rr, cc] = True

    return mask


def stacked_active_contour_model(
    convex_hull_mask: np.ndarray, denoised_image_arr: np.ndarray
) -> np.ndarray:
    """Apply the stacked active contour model from a mask and the corresponding image

    Args:
        convex_hull_mask (np.ndarray): Mask of the convex hull
        denoised_image_arr (np.ndarray): Denoised original image

    Returns:
        np.ndarray: Mask of the convex hull with stacked active contour model applied
    """
    # Get height of the image
    h: int = convex_hull_mask.shape[0]

    # Partition the convex hull mask into upper and lower quadrants
    convex_hull_upper_mask: np.ndarray = convex_hull_mask.copy()
    convex_hull_upper_mask[h // 2 :, :] = False
    convex_hull_lower_mask: np.ndarray = convex_hull_mask.copy()
    convex_hull_lower_mask[: h // 2, :] = False

    # Apply the stacked active contour model
    mask_upper: np.ndarray = apply_stacked_active_contour(
        convex_hull_upper_mask, denoised_image_arr
    )
    mask_lower: np.ndarray = apply_stacked_active_contour(
        convex_hull_lower_mask, denoised_image_arr
    )

    # Merge the two masks from the upper and lower quadrants to reconstruct the lung fields.
    full_mask: np.ndarray = mask_upper | mask_lower

    # Apply smoothing filter to remove jagged edges on the mask boundary
    full_mask: np.ndarray = sk.filters.gaussian(full_mask.astype(float)) > 0.5

    return full_mask


def tvac(ds: FileDataset) -> np.ndarray:
    """Apply the TVAC algorithm on a dicom image

    Args:
        ds (FileDataset): The dicom file object

    Returns:
        np.ndarray: the mask with both lungs
    """
    # Get the pixel array from the dicom file object
    image_arr: np.ndarray = pixel_array(ds)

    # Resize to have a smaller image (better performance)
    original_shape: tuple = image_arr.shape
    h, w = image_arr.shape
    scale = TARGET_SIZE / max(h, w)
    new_h, new_w = int(h * scale), int(w * scale)
    image_arr = sk.transform.resize(image_arr, (new_h, new_w), anti_aliasing=True)

    # Normalize the image with CLAHE algo (Preprocessing)
    normalized_image_arr: np.ndarray = sk.exposure.equalize_adapthist(image_arr)

    # Total variation denoising (Denoised Chest X-Ray)
    denoised_image_arr: np.ndarray = sk.restoration.denoise_tv_chambolle(
        normalized_image_arr
    )

    # Avoid corner problems
    top_cut = int(image_arr.shape[0] * 0.05)
    denoised_image_arr = denoised_image_arr[top_cut:, :]

    # Recursive Thresholding with ISODATA
    # Calculate global threshold with ISODATA
    theta_0: float = sk.filters.threshold_isodata(denoised_image_arr)

    print(f"Initial Theshold: {theta_0}")

    # Get convex hulls as binary masks for each lung
    left_lung_convex_hull_mask, right_lung_convex_hull_mask = recursive_thresholding(
        denoised_image_arr, theta_0
    )

    # Stacked active contour model for both lungs
    left_lung_mask: np.ndarray = stacked_active_contour_model(
        left_lung_convex_hull_mask, denoised_image_arr
    )

    right_lung_mask: np.ndarray = stacked_active_contour_model(
        right_lung_convex_hull_mask, denoised_image_arr
    )

    # Merge the two lung masks
    final_mask: np.ndarray = left_lung_mask | right_lung_mask

    # Add the removed lines to the mask
    final_mask = np.vstack(
        (np.zeros((top_cut, final_mask.shape[1]), dtype=bool), final_mask)
    )

    # Resize to the original size
    final_mask = sk.transform.resize(
        final_mask,
        original_shape,
        order=0,
        preserve_range=True,
        anti_aliasing=False,
    ).astype(bool)

    # Image.fromarray((final_mask * 255).astype(np.uint8)).save("final_mask_4.png")

    return final_mask
