import keyboard
import math


class Triggerbot:
    """Auto-fires when crosshair is over an enemy bounding box."""

    def __init__(self, trigger_key="x"):
        self.enabled = False
        self.trigger_key = trigger_key
        self._was_firing = False

    def toggle(self):
        self.enabled = not self.enabled
        self._was_firing = False

    def tick(self, entities_screen, screen_width, screen_height, mem):
        if not self.enabled:
            if self._was_firing:
                try:
                    mem.write_force_attack(4)
                except:
                    pass
                self._was_firing = False
            return

        if not keyboard.is_pressed(self.trigger_key):
            if self._was_firing:
                try:
                    mem.write_force_attack(4)
                except:
                    pass
                self._was_firing = False
            return

        center_x = screen_width / 2
        center_y = screen_height / 2

        for entity, sx, sy, distance in entities_screen:
            # Estimate bounding box from distance
            box_height = 36000.0 / max(distance, 1.0)
            box_width = box_height / 2

            # Check if crosshair is inside the entity box
            if (abs(sx - center_x) < box_width / 2 and
                    abs(sy - center_y) < box_height / 2):
                try:
                    mem.write_force_attack(5)  # +attack
                except:
                    pass
                self._was_firing = True
                return

        # Crosshair not on any enemy – release fire
        if self._was_firing:
            try:
                mem.write_force_attack(4)  # -attack
            except:
                pass
            self._was_firing = False
