import pygame
import time
import math
import os
import keyboard
from jc.gui_engine import mainWindow
from jc.sprites.menu import MenuSprite
from jc.memory import MemoryAccess
from jc.sprites.esp_border import EspBorder
from jc.aimbot import Aimbot
from jc.bhop import Bhop
from jc.triggerbot import Triggerbot

# ════════════════════════════════════════════════════════════════════════
#  OFFSETS
# ════════════════════════════════════════════════════════════════════════
offsets_config = {
    "m_dwEntityOrigin" : 0x120471C,
    "m_dwViewAngles"   : 0x108AE94,
    "m_dwLocalOrigin"  : 0x13E7F0,
    "m_dwFovScale1"    : 0xEC9E20,
    "m_dwGetTeam"      : 0x100DF4,
    "m_dwPunchAngles"  : 0x122E324,
    "m_dwOnGround"     : 0x122E2D4,
    "m_dwForceJump"    : 0x131434,
    "m_dwForceAttack"  : 0x131370,
    "m_dwWeaponId"     : 0x108DD90,
}
player_fov = 100

# ════════════════════════════════════════════════════════════════════════
#  WEAPON ID → NAME MAP
# ════════════════════════════════════════════════════════════════════════
WEAPON_NAMES = {
    1: "P228", 2: "SHIELD", 3: "SCOUT", 4: "HE NADE", 5: "XM1014",
    6: "C4", 7: "MAC10", 8: "AUG", 9: "SMOKE", 10: "ELITE",
    11: "FIVESEVEN", 12: "UMP45", 13: "SG550", 14: "GALIL", 15: "FAMAS",
    16: "USP", 17: "GLOCK", 18: "AWP", 19: "MP5", 20: "M249",
    21: "M3", 22: "M4A1", 23: "TMP", 24: "G3SG1", 25: "FLASH",
    26: "DEAGLE", 27: "SG552", 28: "AK47", 29: "KNIFE", 30: "P90",
}

# ════════════════════════════════════════════════════════════════════════
#  INIT
# ════════════════════════════════════════════════════════════════════════
window = mainWindow()

mem = MemoryAccess(
    offsets = offsets_config,
    pid    = window.get_pid()
)

# Feature instances
aimbot     = Aimbot(fov_limit_pixels=180, smooth_factor=1.0,
                    trigger_key="shift", sensitivity=0.22)
bhop       = Bhop(trigger_key="space")
triggerbot = Triggerbot(trigger_key="x")

ms = MenuSprite()
clock = pygame.time.Clock()

# ════════════════════════════════════════════════════════════════════════
#  TOGGLE FLAGS  (visual features)
# ════════════════════════════════════════════════════════════════════════
show_snaplines = True
show_radar     = True
show_fov_circle = True

# ════════════════════════════════════════════════════════════════════════
#  KEY CONFIG
# ════════════════════════════════════════════════════════════════════════
keys_config = {
    "OpenMenu"        : "INSERT",
    "ToggleAimbot"    : "CAPSLOCK",
    "ToggleBhop"      : "F1",
    "ToggleTrigger"   : "F2",
    "ToggleSnaplines" : "F4",
    "ToggleRadar"     : "F5",
    "ToggleFovCircle" : "F6",
    "IncreaseFov"     : "]",
    "DecreaseFov"     : "[",
}

def check_key(action):
    key = keys_config.get(action, action)
    if keyboard.is_pressed(key):
        while keyboard.is_pressed(key):
            pass
        return True
    return False

# ════════════════════════════════════════════════════════════════════════
#  WORLD → SCREEN
# ════════════════════════════════════════════════════════════════════════
import math

def world_to_screen(px, py, pz, yaw, pitch, ox, oy, oz, screen_width, screen_height, fov = 100):
    yaw = math.radians(yaw)
    pitch = math.radians(pitch)
    fov = math.radians(fov)
    
    dx = ox - px
    dy = oy - py
    dz = oz - pz
    
    distance = math.sqrt(dx**2 + dy**2 + dz**2)
    
    cos_yaw = math.cos(yaw)
    sin_yaw = math.sin(yaw)
    
    cos_pitch = math.cos(pitch)
    sin_pitch = math.sin(pitch)
    
    rot_x = dx * cos_yaw + dz * sin_yaw
    rot_z = -dx * sin_yaw + dz * cos_yaw
    
    rot_y = dy * cos_pitch - rot_z * sin_pitch
    rot_z = dy * sin_pitch + rot_z * cos_pitch
    
    if rot_z <= 0:
        return None, None, distance  # Behind player
    
    fov_scale = 1 / math.tan(fov / 2)
    
    screen_x = (rot_x / rot_z) * fov_scale
    screen_y = (rot_y / rot_z) * fov_scale * (screen_width / screen_height)
    
    pixel_x = (screen_width / 2) * (1 + screen_x)
    pixel_y = (screen_height / 2) * (1 - screen_y)
    
    if 0 <= pixel_x <= screen_width and 0 <= pixel_y <= screen_height:
        return pixel_x, pixel_y, distance
    else:
        return None, None, distance 

# ════════════════════════════════════════════════════════════════════════
#  FONTS
# ════════════════════════════════════════════════════════════════════════
pygame.font.init()
_status_font  = pygame.font.SysFont("Consolas", 14)
_radar_font   = pygame.font.SysFont("Consolas", 10)

# ════════════════════════════════════════════════════════════════════════
#  DRAW CALLBACK  (snaplines, fov circle, radar, weapon – raw surface)
# ════════════════════════════════════════════════════════════════════════
_draw_data = {}   # populated each frame before window.update()

def _overlay_draw(surface):
    """Called by gui_engine between fill and sprite blit."""
    sw = surface.get_width()
    sh = surface.get_height()
    cx, cy = sw // 2, sh // 2

    entities = _draw_data.get("entities", [])

    # ── SNAPLINES ──
    if show_snaplines:
        for entity, ex, ey, dist in entities:
            alpha = max(40, 255 - int(dist / 8))
            color = (255, 255, 50, alpha)
            pygame.draw.line(surface, color, (cx, sh), (int(ex), int(ey)), 1)

    # ── FOV CIRCLE ──
    if show_fov_circle:
        radius = _draw_data.get("fov_radius", 180)
        pygame.draw.circle(surface, (255, 255, 255, 60), (cx, cy), int(radius), 1)

    # ── 2D RADAR ──
    if show_radar:
        _draw_radar(surface, entities)


def _draw_radar(surface, entities):
    """Draw a small 2D radar in the top-right corner."""
    rw, rh = 140, 140
    padding = 10
    sx = surface.get_width() - rw - padding
    sy = padding
    center_x = sx + rw // 2
    center_y = sy + rh // 2
    radar_range = 3000.0   # world units visible on radar

    # background
    bg = pygame.Surface((rw, rh), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 120))
    pygame.draw.rect(bg, (255, 255, 255, 80), (0, 0, rw, rh), 1)
    surface.blit(bg, (sx, sy))

    # crosshair on radar centre
    pygame.draw.line(surface, (255, 255, 255, 80),
                     (center_x - 4, center_y), (center_x + 4, center_y), 1)
    pygame.draw.line(surface, (255, 255, 255, 80),
                     (center_x, center_y - 4), (center_x, center_y + 4), 1)

    # player yaw for rotation
    yaw_rad = math.radians(_draw_data.get("yaw", 0) + 270)
    cos_y = math.cos(yaw_rad)
    sin_y = math.sin(yaw_rad)

    lx = _draw_data.get("lx", 0)
    lz = _draw_data.get("lz", 0)

    for entity, ex, ey, dist in entities:
        # world delta
        dx = entity["x"] - lx
        dz = entity["z"] - lz

        # rotate into view-relative coordinates
        rx = dx * cos_y + dz * sin_y
        ry = -dx * sin_y + dz * cos_y

        # scale to radar pixels
        px = int(center_x + (rx / radar_range) * (rw / 2))
        py = int(center_y - (ry / radar_range) * (rh / 2))

        # clamp inside radar bounds
        px = max(sx + 2, min(sx + rw - 2, px))
        py = max(sy + 2, min(sy + rh - 2, py))

        if dist < 500:
            dot_color = (255, 50, 50)
        elif dist < 1500:
            dot_color = (255, 200, 50)
        else:
            dot_color = (50, 200, 255)

        pygame.draw.circle(surface, dot_color, (px, py), 3)

    # label
    label = _radar_font.render("RADAR", True, (200, 200, 200))
    surface.blit(label, (sx + 4, sy + 2))


# ════════════════════════════════════════════════════════════════════════
#  MAIN LOOP
# ════════════════════════════════════════════════════════════════════════
while True:
    clock.tick(60)
    timedump = time.time()
    mem.update()

    # ── key toggles ──
    if check_key("ToggleAimbot"):
        aimbot.toggle()
    if check_key("ToggleBhop"):
        bhop.toggle()
    if check_key("ToggleTrigger"):
        triggerbot.toggle()
    if check_key("ToggleSnaplines"):
        show_snaplines = not show_snaplines
    if check_key("ToggleRadar"):
        show_radar = not show_radar
    if check_key("ToggleFovCircle"):
        show_fov_circle = not show_fov_circle

    # FOV Circle size adjustments
    if keyboard.is_pressed(keys_config["IncreaseFov"]):
        aimbot.fov_limit_pixels = min(1000, aimbot.fov_limit_pixels + 5)
    if keyboard.is_pressed(keys_config["DecreaseFov"]):
        aimbot.fov_limit_pixels = max(10, aimbot.fov_limit_pixels - 5)

    # ── world → screen for all visible enemies ──
    entities_screen = []
    width, height, left, top = window.get_sizes(window.get_target_window())
    for entity in mem.entities_list:
        boxpos = world_to_screen(
            mem.local_player_x,
            mem.local_player_y, 
            mem.local_player_z,
            mem.local_player_yaw + 270, 
            0 - mem.local_player_pitch,
            entity["x"],
            entity["y"], 
            entity["z"],
            width, 
            height,
            fov = player_fov / (mem.local_player_fov_scale + 0.161) 
        )
        if boxpos is not None:
            x, y, distance = boxpos
            if x is not None and y is not None:
                # Skip teammates: only show ESP for enemies
                entity_team = entity.get("team", 0)
                if entity_team != 0 and mem.local_player_team != 0 and entity_team == mem.local_player_team:
                    continue
                entities_screen.append((entity, x, y, distance))

    # ── combat ticks ──
    aimbot.tick(entities_screen, width, height)
    triggerbot.tick(entities_screen, width, height, mem)
    bhop.tick(mem)

    # ── build ESP sprites ──
    window.esp_list = pygame.sprite.Group()
    for entity, x, y, distance in entities_screen:
        is_target = (aimbot.locked_entity is not None and
                     entity is aimbot.locked_entity)
        sprite = EspBorder(x, y, distance,
                           name=entity.get("name", ""),
                           highlight=is_target)
        window.esp_list.add(sprite)

    # ── status HUD (left side) ──
    hud_lines = [
        ("AIMBOT",    aimbot.enabled,     "CAPSLOCK"),
        ("BHOP",      bhop.enabled,       "F1"),
        ("TRIGGER",   triggerbot.enabled,  "F2"),
        ("SNAPLINES", show_snaplines,     "F4"),
        ("RADAR",     show_radar,         "F5"),
        ("FOV CIRCLE",show_fov_circle,    "F6"),
    ]
    for i, (label, active, key) in enumerate(hud_lines):
        state = "ON" if active else "OFF"
        color = (0, 255, 0) if active else (255, 70, 70)
        txt = f"[{key}] {label}: {state}"
        surf = _status_font.render(txt, True, color)
        sp = pygame.sprite.Sprite()
        sp.image = surf
        sp.rect = surf.get_rect(topleft=(10, 10 + i * 18))
        window.esp_list.add(sp)

    # ── weapon ID display ──
    wep_name = WEAPON_NAMES.get(mem.weapon_id, f"ID:{mem.weapon_id}")
    wep_surf = _status_font.render(f"WEAPON: {wep_name}", True, (180, 220, 255))
    wep_sp = pygame.sprite.Sprite()
    wep_sp.image = wep_surf
    wep_sp.rect = wep_surf.get_rect(topleft=(10, 10 + len(hud_lines) * 18 + 6))
    window.esp_list.add(wep_sp)

    # ── FOV circle size display ──
    fov_surf = _status_font.render(f"FOV SIZE: {aimbot.fov_limit_pixels}px ([,])", True, (240, 240, 240))
    fov_sp = pygame.sprite.Sprite()
    fov_sp.image = fov_surf
    fov_sp.rect = fov_surf.get_rect(topleft=(10, 10 + len(hud_lines) * 18 + 6 + 18))
    window.esp_list.add(fov_sp)

    # ── populate draw data for the overlay callback ──
    _draw_data["entities"]   = entities_screen
    _draw_data["fov_radius"] = aimbot.fov_limit_pixels
    _draw_data["yaw"]        = mem.local_player_yaw
    _draw_data["lx"]         = mem.local_player_x
    _draw_data["lz"]         = mem.local_player_z

    time.sleep(max(0, time.time() - timedump - 0.016))
    window.update(draw_callback=_overlay_draw)