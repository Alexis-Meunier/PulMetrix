import math
import numpy as np
import numpy.typing as npt
import skimage as sk
import typing as ty

from pydicom.dataset import FileDataset

from src.utils.point import Point

def c(n: int) -> float:
    return 350 / math.sqrt(n)

def compute_statistics(stored_values: npt.NDArray[np.double], n: int) -> ty.Tuple[np.double, np.double, np.double]:
    seen_values = stored_values[:n]
    mean = np.median(seen_values)

    ld = np.std(seen_values[seen_values < mean]).astype(np.double)
    ud = np.std(seen_values[seen_values > mean]).astype(np.double)

    return mean, ld, ud

def compute_threshold(mean: np.double, ld: np.double, ud: np.double, w: float, n: int) -> ty.Tuple[np.double, np.double]:
    t_upper = mean + (ud * w + c(n))
    t_lower = mean - (ld * w + c(n))
    return t_lower, t_upper

def compute_region(seed: Point, image: npt.NDArray[np.double]) -> ty.Tuple[np.double, np.double, np.double, int, int]:
    # init mask, stack and currently seen values
    h, w = image.shape
    mask = np.zeros_like(image, dtype=np.bool)
    stored_values = np.zeros(h * w)
    random_stack = np.zeros(h * w * 2, dtype=np.int32).reshape(w * h, 2)

    # init thresholds
    x, y = seed.x, seed.y
    r = 1
    
    surrounding_seed = image[y-r:y+r+1, x-r:x+r+1].flatten()
    mean, ld, ud = compute_statistics(surrounding_seed, 9)
    n_compute = 1
    t_lower, t_upper= compute_threshold(mean, ld, ud, 1.5, 9)

    # surrounding_seed is considered good
    n = (2 * r + 1) * (2 * r + 1)
    n_init = n
    stored_values[:n] = surrounding_seed 
    mask[y-r:y+r+1, x-r:x+r+1] = 1

    stack_len = (2 * r + 1) * (2 * r + 1) - 1

    neighbors = np.array([
        [-1, -1], [-1, 0], [-1, 1],
        [0, -1] ,          [0, 1] ,
        [1, -1] , [1, 0] , [1, 1]
    ])

    random_stack[:stack_len] = np.array([y, x]) + neighbors

    # iterative way cause recursion exceed limit haha

    while stack_len != 0:
        # random march
        rand_i = np.random.randint(0, stack_len)
        random_stack[rand_i], random_stack[stack_len - 1] = random_stack[stack_len - 1].copy(), random_stack[rand_i].copy()

        # simulate stack.pop()
        stack_len -= 1
        current = random_stack[stack_len]

        ns = np.zeros(8).reshape(4, 2).astype(np.int32)
        y, x = current
        n_count = 0

        if x - 1 >= 0:
            ns[n_count] = np.array([y, x - 1])
            n_count += 1

        if x + 1 < w:
            ns[n_count] = np.array([y, x + 1])
            n_count += 1

        if y - 1 >= 0:
            ns[n_count] = np.array([y - 1, x])
            n_count += 1

        if y + 1 < h:
            ns[n_count] = np.array([y + 1, x])
            n_count += 1

        # print(current, image[current])
        for n_i in range(n_count):
            n_y, n_x = ns[n_i]
            if mask[n_y, n_x] == 0 and t_lower <= image[n_y, n_x] <= t_upper:
                mask[n_y, n_x] = 1
                
                # simulate stack.append()
                random_stack[stack_len] = ns[n_i]
                stack_len += 1 
                stored_values[n] = image[n_y, n_x]
                n += 1

                # update thresholds if needed
                if n == n_init * 2:
                    n_init = n
                    n_compute += 1
                    mean, ld, ud = compute_statistics(stored_values, n)
                    t_lower, t_upper = compute_threshold(mean, ld, ud, 1.5, n)
                
    return mean, ld, ud, n, n_compute


def propagate_region(seed: Point, image: npt.NDArray[np.double], mean: np.double, ld: np.double, ud: np.double, n: int, n_compute: int) -> npt.NDArray[np.bool]:
    # init mask, stack and currently seen values
    h, w = image.shape
    mask = np.zeros_like(image, dtype=np.bool)
    stack = np.zeros(h * w * 2, dtype=np.int32).reshape(w * h, 2)

    # init thresholds
    x, y = seed.x, seed.y
    
    coeff = 1 + (n_compute - 1) * 0.15
    t_lower, t_upper= compute_threshold(mean, ld * coeff, ud * coeff, 2.58, n)

    # seed is considered good
    mask[y, x] = 1
    stack_len = 1
    stack[0] = np.array([y, x])

    # iterative way cause recursion exceed limit haha

    while stack_len != 0:
        # simulate stack.pop()
        stack_len -= 1
        current = stack[stack_len]

        ns = np.zeros(8).reshape(4, 2).astype(np.int32)
        y, x = current
        n_count = 0

        if x - 1 >= 0:
            ns[n_count] = np.array([y, x - 1])
            n_count += 1

        if x + 1 < w:
            ns[n_count] = np.array([y, x + 1])
            n_count += 1

        if y - 1 >= 0:
            ns[n_count] = np.array([y - 1, x])
            n_count += 1

        if y + 1 < h:
            ns[n_count] = np.array([y + 1, x])
            n_count += 1

        for n_i in range(n_count):
            n_y, n_x = ns[n_i]
            if mask[n_y, n_x] == 0 and t_lower <= image[n_y, n_x] <= t_upper:
                mask[n_y, n_x] = 1
                
                # simulate stack.append()
                stack[stack_len] = ns[n_i]
                stack_len += 1 
        
    return mask


def region_growing(seeds: ty.List[Point], image: FileDataset) -> npt.NDArray[np.bool]:
    array = image.pixel_array
    original_shape = array.shape

    r_y, r_x = 1000 / array.shape[0], 1000 / array.shape[1]
    
    array = sk.transform.resize(array, (1000, 1000), order=0, preserve_range=True, anti_aliasing=False).astype(dtype=np.double)
    array = array / np.max(array) * 255

    mask = np.zeros_like(array, dtype=np.bool)

    for seed in seeds:
        seed.x = int(seed.x * r_x)
        seed.y = int(seed.y * r_y)

        mean, ld, ud, n, n_compute = compute_region(seed, array)
        cur_mask = propagate_region(seed, array, mean, ld, ud, n, n_compute)
        mask |= cur_mask

    ball = sk.morphology.disk(20)
    sk.morphology.closing(mask, ball, out=mask)
    mask = sk.transform.resize(mask, original_shape, order=0, preserve_range=True, anti_aliasing=False)
    return mask