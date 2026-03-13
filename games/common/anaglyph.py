import pygame
import pygame.surfarray


MODE_GLASSES = "glasses"
FILTER_LR = "left_red_right_blue"
FILTER_RL = "left_blue_right_red"

GLASSES_BACKGROUND = (255, 19, 255, 179)
RED_FILTER = (255, 0, 0, 255)
BLUE_FILTER = (0, 0, 255, 255)


def apply_filter(base, mode, filter_direction, side, mode_glasses=MODE_GLASSES, filter_lr=FILTER_LR):
    if mode != mode_glasses:
        return base
    is_left_red = filter_direction == filter_lr
    use_red = (side == "left" and is_left_red) or (side == "right" and not is_left_red)
    color = RED_FILTER if use_red else BLUE_FILTER
    result = pygame.Surface(base.get_size(), pygame.SRCALPHA)
    result.fill(color)
    base_alpha = pygame.surfarray.array_alpha(base)
    result_alpha = pygame.surfarray.pixels_alpha(result)
    tint_alpha = color[3]
    result_alpha[:] = (base_alpha.astype("uint16") * tint_alpha // 255).astype("uint8")
    del result_alpha
    return result


def blend_filtered_patterns(canvas_size, left_surface, left_rect, right_surface, right_rect):
    left_layer = pygame.Surface(canvas_size, pygame.SRCALPHA)
    right_layer = pygame.Surface(canvas_size, pygame.SRCALPHA)
    left_layer.blit(left_surface, left_rect)
    right_layer.blit(right_surface, right_rect)

    left_rgb = pygame.surfarray.array3d(left_layer).astype("uint16")
    right_rgb = pygame.surfarray.array3d(right_layer).astype("uint16")
    left_alpha = pygame.surfarray.array_alpha(left_layer).astype("uint16")
    right_alpha = pygame.surfarray.array_alpha(right_layer).astype("uint16")

    output_rgb = left_rgb.copy()
    output_alpha = left_alpha.copy()

    only_right = (left_alpha == 0) & (right_alpha > 0)
    output_rgb[only_right] = right_rgb[only_right]
    output_alpha[only_right] = right_alpha[only_right]

    overlap = (left_alpha > 0) & (right_alpha > 0)
    if overlap.any():
        output_rgb[overlap] = (left_rgb[overlap] * right_rgb[overlap]) // 255
        output_alpha[overlap] = left_alpha[overlap] + right_alpha[overlap] - (
            left_alpha[overlap] * right_alpha[overlap] // 255
        )

    blended = pygame.Surface(canvas_size, pygame.SRCALPHA)
    blended_rgb = pygame.surfarray.pixels3d(blended)
    blended_rgb[:] = output_rgb.astype("uint8")
    del blended_rgb
    blended_alpha = pygame.surfarray.pixels_alpha(blended)
    blended_alpha[:] = output_alpha.astype("uint8")
    del blended_alpha
    return blended
