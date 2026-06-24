import keyboard


class Bhop:
    """Bunny hop: auto-jumps when holding space while on the ground."""

    def __init__(self, trigger_key="space"):
        self.enabled = False
        self.trigger_key = trigger_key

    def toggle(self):
        self.enabled = not self.enabled

    def tick(self, mem):
        if not self.enabled:
            return
        if not keyboard.is_pressed(self.trigger_key):
            return
        # on_ground flag: non-zero means player is on the ground
        try:
            if mem.on_ground & 1:
                mem.write_force_jump(5)   # +jump
            else:
                mem.write_force_jump(4)   # -jump
        except:
            pass
