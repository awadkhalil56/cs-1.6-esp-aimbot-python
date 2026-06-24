import pygame
import win32gui
import win32con
import pygetwindow as gw
import win32process

class mainWindow:
    def __init__(self):
        pygame.init()
        self.cs_title = "Counter-Strike"
        self.main_list = pygame.sprite.Group()
        self.esp_list = pygame.sprite.Group()
        self.Screen = pygame.display.set_mode((100, 100), pygame.NOFRAME | pygame.SRCALPHA | pygame.HWSURFACE)
        self.Screen, self.Width, self.Height = self._set_window_transparent(self._get_pygame_hwnd(), self.get_target_window())
    
    def update(self, draw_callback=None):
        self.Screen = self._update_position(self._get_pygame_hwnd(), self.Screen, self.get_target_window())
        self.Screen.fill((0, 0, 0, 0))
        if draw_callback:
            draw_callback(self.Screen)
        self.main_list.draw(self.Screen)
        self.esp_list.draw(self.Screen)
        pygame.display.flip()

    def get_pid(self):
        window = gw.getWindowsWithTitle(self.cs_title)[0]
        hwnd = window._hWnd  
        _, pid = win32process.GetWindowThreadProcessId(hwnd) 
        return pid

    def get_target_window(self):
        window = gw.getWindowsWithTitle(self.cs_title)[0]
        return window
    
    def _get_pygame_hwnd(self):
        hwnd = pygame.display.get_wm_info()['window']
        return hwnd
    def get_sizes(self, target_window):
        rect = win32gui.GetWindowRect(target_window._hWnd)
        left, top, right, bottom = rect[0], rect[1], rect[2], rect[3]
        width = right - left
        height = bottom - top
        return (width, height, left, top)

    def _set_window_transparent(self, hwnd, target_window):
        target_hwnd = target_window._hWnd
        
        # Programmatically make the CS 1.6 window borderless
        style = win32gui.GetWindowLong(target_hwnd, win32con.GWL_STYLE)
        style &= ~win32con.WS_CAPTION
        style &= ~win32con.WS_THICKFRAME
        style &= ~win32con.WS_MINIMIZEBOX
        style &= ~win32con.WS_MAXIMIZEBOX
        style &= ~win32con.WS_SYSMENU
        win32gui.SetWindowLong(target_hwnd, win32con.GWL_STYLE, style)
        
        # Stretch it to cover the full screen size
        import win32api
        screen_width = win32api.GetSystemMetrics(0)
        screen_height = win32api.GetSystemMetrics(1)
        win32gui.SetWindowPos(target_hwnd, win32con.HWND_NOTOPMOST, 0, 0, screen_width, screen_height, win32con.SWP_FRAMECHANGED)
        
        # Now set up the Pygame transparent overlay window to match
        width, height, left, top = self.get_sizes(target_window)
        screen = pygame.display.set_mode((width, height), pygame.NOFRAME | pygame.SRCALPHA | pygame.HWSURFACE)
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, left, top, width, height, 0)
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)
        win32gui.SetLayeredWindowAttributes(hwnd, 0, 0, win32con.LWA_COLORKEY)
        return screen, width, height
    
    def _update_position(self, hwnd, screen, target_window):
        width, height, left, top = self.get_sizes(target_window)
        if screen.get_width() != width or screen.get_height() != height:
            screen = pygame.display.set_mode((width, height), pygame.NOFRAME | pygame.SRCALPHA | pygame.HWSURFACE)
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, left, top, width, height, 0)
        return screen