import numpy as np
import pygame
import pygame.surfarray

try:
    import cv2
except ImportError:
    cv2 = None


MODE_GLASSES = "glasses"
FILTER_LR = "left_red_right_blue"
FILTER_RL = "left_blue_right_red"

GLASSES_BACKGROUND = (255, 19, 255, 179)
SUBTRACTIVE_BACKGROUND = (255, 0, 255, 255)
RED_FILTER = (255, 0, 0, 255)
BLUE_FILTER = (0, 0, 255, 255)
GLASSES_BUTTON_COLOR = (134, 142, 176)


def apply_filter(base, mode, filter_direction, side, mode_glasses=MODE_GLASSES, filter_lr=FILTER_LR):
    if mode != mode_glasses:
        return base
    is_left_red = filter_direction == filter_lr
    use_red = (side == "left" and is_left_red) or (side == "right" and not is_left_red)
    base_alpha = pygame.surfarray.array_alpha(base)
    result_rgb = np.zeros((*base_alpha.shape, 3), dtype=np.uint8)
    channel_index = 0 if use_red else 2
    result_rgb[:, :, channel_index] = base_alpha
    result = pygame.Surface(base.get_size(), pygame.SRCALPHA)
    pixels_rgb = pygame.surfarray.pixels3d(result)
    pixels_rgb[:] = result_rgb
    del pixels_rgb
    result_alpha = pygame.surfarray.pixels_alpha(result)
    result_alpha[:] = base_alpha
    del result_alpha
    return result


def _clear_edge_artifacts(rgb, alpha, crop_border):
    crop_x, crop_y = crop_border if isinstance(crop_border, tuple) else (crop_border, crop_border)
    crop_x = max(0, int(crop_x))
    crop_y = max(0, int(crop_y))
    if crop_x:
        rgb[:crop_x, :, :] = 0
        rgb[-crop_x:, :, :] = 0
        alpha[:crop_x, :] = 0
        alpha[-crop_x:, :] = 0
    if crop_y:
        rgb[:, :crop_y, :] = 0
        rgb[:, -crop_y:, :] = 0
        alpha[:, :crop_y] = 0
        alpha[:, -crop_y:] = 0


def _rect_offset_crop(left_rect, right_rect):
    dx = abs(int(right_rect[0]) - int(left_rect[0]))
    dy = abs(int(right_rect[1]) - int(left_rect[1]))
    return dx, dy


def _bitwise_overlap(left_rgb, right_rgb, overlap_mask):
    if cv2 is not None:
        left_hw = np.transpose(left_rgb, (1, 0, 2))
        right_hw = np.transpose(right_rgb, (1, 0, 2))
        overlap_hw = np.transpose(overlap_mask, (1, 0))
        overlap_rgb = cv2.bitwise_and(left_hw, right_hw)
        blended_hw = np.zeros_like(left_hw)
        blended_hw[overlap_hw] = overlap_rgb[overlap_hw]
        return np.transpose(blended_hw, (1, 0, 2))
    result = np.zeros_like(left_rgb)
    result[overlap_mask] = np.bitwise_and(left_rgb[overlap_mask], right_rgb[overlap_mask])
    return result


def blend_filtered_patterns(canvas_size, left_surface, left_rect, right_surface, right_rect, crop_border=0):
    left_layer = pygame.Surface(canvas_size, pygame.SRCALPHA)
    right_layer = pygame.Surface(canvas_size, pygame.SRCALPHA)
    left_layer.blit(left_surface, left_rect)
    right_layer.blit(right_surface, right_rect)

    left_rgb = pygame.surfarray.array3d(left_layer)
    right_rgb = pygame.surfarray.array3d(right_layer)
    left_alpha = pygame.surfarray.array_alpha(left_layer)
    right_alpha = pygame.surfarray.array_alpha(right_layer)

    output_rgb = np.zeros_like(left_rgb)
    output_alpha = np.zeros_like(left_alpha)

    only_left = (left_alpha > 0) & (right_alpha == 0)
    output_rgb[only_left] = left_rgb[only_left]
    output_alpha[only_left] = left_alpha[only_left]

    only_right = (left_alpha == 0) & (right_alpha > 0)
    output_rgb[only_right] = right_rgb[only_right]
    output_alpha[only_right] = right_alpha[only_right]

    overlap = (left_alpha > 0) & (right_alpha > 0)
    if overlap.any():
        overlap_rgb = _bitwise_overlap(left_rgb, right_rgb, overlap)
        output_rgb[overlap] = overlap_rgb[overlap]
        output_alpha[overlap] = np.maximum(left_alpha[overlap], right_alpha[overlap])

    total_crop = _rect_offset_crop(left_rect, right_rect)
    extra_crop = crop_border if isinstance(crop_border, tuple) else (crop_border, crop_border)
    crop = (
        max(total_crop[0], int(extra_crop[0])),
        max(total_crop[1], int(extra_crop[1])),
    )
    if crop[0] or crop[1]:
        _clear_edge_artifacts(output_rgb, output_alpha, crop)

    blended = pygame.Surface(canvas_size, pygame.SRCALPHA)
    blended_rgb = pygame.surfarray.pixels3d(blended)
    blended_rgb[:] = output_rgb
    del blended_rgb
    blended_alpha = pygame.surfarray.pixels_alpha(blended)
    blended_alpha[:] = output_alpha
    del blended_alpha
    return blended
