import pygame

pygame.font.init()
_esp_font = pygame.font.SysFont("Consolas", 12)


class EspBorder(pygame.sprite.Sprite):
    """ESP box with name, distance, head dot, and distance-based coloring."""

    def __init__(self, x, y, distance, name="", highlight=False):
        super().__init__()

        # ── box size from distance ──
        sized = distance / 2000
        box_w = max(9 / sized, 4)
        box_h = max(18 / sized, 8)

        # ── colour by distance ──
        if highlight:
            color = (0, 255, 0)          # aimbot lock: green
        elif distance < 500:
            color = (255, 50, 50)        # close: red
        elif distance < 1500:
            color = (255, 200, 50)       # mid: yellow
        else:
            color = (50, 200, 255)       # far: cyan

        # ── prepare text surfaces ──
        name_surf = None
        dist_surf = None
        name_h = 0
        dist_h = 0
        text_w = 0

        if name:
            name_surf = _esp_font.render(name, True, (255, 255, 255))
            name_h = name_surf.get_height() + 2
            text_w = max(text_w, name_surf.get_width())

        dist_text = f"{int(distance)}u"
        dist_surf = _esp_font.render(dist_text, True, (200, 200, 200))
        dist_h = dist_surf.get_height() + 2
        text_w = max(text_w, dist_surf.get_width())

        # ── canvas big enough for box + text + head dot ──
        head_r = max(int(3 / sized), 2)
        total_w = max(box_w, text_w) + head_r * 2 + 4
        total_h = name_h + box_h + dist_h + head_r * 2 + 4

        self.image = pygame.Surface((total_w, total_h), pygame.SRCALPHA)

        # offsets so box is centred horizontally
        ox = total_w / 2 - box_w / 2
        oy = name_h + head_r * 2 + 2

        # ── head dot ──
        head_cx = int(total_w / 2)
        head_cy = int(name_h + head_r)
        pygame.draw.circle(self.image, color, (head_cx, head_cy), head_r)

        # ── box outline ──
        pygame.draw.rect(self.image, color,
                         (ox, oy, box_w, box_h), 1)

        # ── name above head ──
        if name_surf:
            nx = (total_w - name_surf.get_width()) / 2
            self.image.blit(name_surf, (nx, 0))

        # ── distance below box ──
        if dist_surf:
            dx = (total_w - dist_surf.get_width()) / 2
            self.image.blit(dist_surf, (dx, oy + box_h + 2))

        # ── position on overlay ──
        self.rect = self.image.get_rect(
            center=(int(x), int(y))
        )
