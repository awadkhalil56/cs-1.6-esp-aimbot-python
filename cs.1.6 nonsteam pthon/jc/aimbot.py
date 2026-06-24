import ctypes
import math
import keyboard


class Aimbot:
    def __init__(self, fov_limit_pixels=180, smooth_factor=4.0, trigger_key="shift", sensitivity=0.22):
        """
        fov_limit_pixels: max distance in screen pixels from crosshair to lock on
        smooth_factor   : divisor to smooth out movements (higher = smoother)
        trigger_key     : key to hold to aim
        sensitivity     : multiplier for mouse movement step
        """
        self.enabled = False
        self.fov_limit_pixels = fov_limit_pixels
        self.smooth_factor = max(smooth_factor, 1.0)
        self.trigger_key = trigger_key
        self.sensitivity = sensitivity
        self.locked_entity = None  # current target entity

    def toggle(self):
        self.enabled = not self.enabled
        self.locked_entity = None

    def tick(self, entities_with_screen, screen_width, screen_height):
        """Call each frame with entities that have valid screen positions."""
        self.locked_entity = None

        if not self.enabled:
            return

        # Check if the trigger key is held (case-insensitive)
        if not (keyboard.is_pressed(self.trigger_key) or 
                keyboard.is_pressed(self.trigger_key.lower()) or 
                keyboard.is_pressed(self.trigger_key.upper())):
            return

        center_x = screen_width / 2
        center_y = screen_height / 2

        best_target = None
        min_dist = self.fov_limit_pixels

        for entity, sx, sy, distance in entities_with_screen:
            if sx is None or sy is None:
                continue

            # Calculate box height in pixels to offset target to head level
            box_height = 36000.0 / max(distance, 1.0)
            target_y = sy - (box_height * 0.42) # Aim at upper chest/head area

            # Calculate screen distance from crosshair
            dist = math.hypot(sx - center_x, target_y - center_y)
            if dist < min_dist:
                min_dist = dist
                best_target = (entity, sx, target_y)

        if best_target is None:
            return

        entity, target_x, target_y = best_target
        self.locked_entity = entity

        # Proportional feedback deltas
        dx = target_x - center_x
        dy = target_y - center_y

        # Scale by sensitivity and apply smoothing
        move_x = (dx * self.sensitivity) / self.smooth_factor
        move_y = (dy * self.sensitivity) / self.smooth_factor

        # Execute relative mouse movement
        # MOUSEEVENTF_MOVE = 0x0001
        ctypes.windll.user32.mouse_event(0x0001, int(move_x), int(move_y), 0, 0)
