from pymem import Pymem
from pymem.process import module_from_name
import time 

class MemoryAccess:
    def __init__(self, pid, offsets):
        self.offsets = offsets
        
        self.pm = Pymem()
        self.pm.open_process_from_id(pid)
        self.client = module_from_name(self.pm.process_handle, "client.dll").lpBaseOfDll
        self.hw = module_from_name(self.pm.process_handle, "hw.dll").lpBaseOfDll
        self.entities_list_full = self.get_entity()
        
    def get_entity(self):
        players = []
        for i in range(0, 256):
            player_offset = i * 0x250



            player = {
                "name" : self.pm.read_string(self.hw + self.offsets["m_dwEntityOrigin"] + player_offset),
                "x" : self.pm.read_float(self.hw + self.offsets["m_dwEntityOrigin"] + 0x84 + player_offset),
                "z" : self.pm.read_float(self.hw + self.offsets["m_dwEntityOrigin"] + 0x88 + player_offset),
                "y" : self.pm.read_float(self.hw + self.offsets["m_dwEntityOrigin"] + 0x8C + player_offset),
                "timer" : self.pm.read_float(self.hw + self.offsets["m_dwEntityOrigin"] + 0x7C + player_offset)

            }
            # Determine team from player model name (offset 0x2C within entity struct)
            try:
                model = self.pm.read_string(self.hw + self.offsets["m_dwEntityOrigin"] + 0x2C + player_offset).lower()
                ct_models = ("gign", "gsg9", "sas", "urban", "vip")
                t_models = ("leet", "arctic", "guerilla", "terror")
                if any(m in model for m in ct_models):
                    player["team"] = 2  # CT
                elif any(m in model for m in t_models):
                    player["team"] = 1  # T
                else:
                    player["team"] = 0  # Unknown
            except:
                player["team"] = 0
            if not player["name"] == '':
                players.append(player)
        return players

    def remove_inactive(self, first_read, second_read):
        final = []
        for i in range(0, len(second_read)):
            try:
                if not first_read[i]["timer"] == second_read[i]["timer"]:
                    final.append(second_read[i])
            except:
                pass
        return final




    def update(self):
        self.local_player_pitch = self.pm.read_float(self.hw + self.offsets["m_dwViewAngles"])
        self.local_player_yaw = self.pm.read_float(self.hw + self.offsets["m_dwViewAngles"] + 0x4)
        self.local_player_x = self.pm.read_float(self.client + self.offsets["m_dwLocalOrigin"])
        self.local_player_z = self.pm.read_float(self.client + self.offsets["m_dwLocalOrigin"] + 0x4)
        self.local_player_y = self.pm.read_float(self.client + self.offsets["m_dwLocalOrigin"] + 0x8)
        self.local_player_fov_scale = self.pm.read_float(self.hw + self.offsets["m_dwFovScale1"])
        # Read local player team (1=T, 2=CT)
        try:
            self.local_player_team = self.pm.read_int(self.client + self.offsets["m_dwGetTeam"])
        except:
            self.local_player_team = 0
        # Read punch angles for recoil control
        try:
            self.punch_pitch = self.pm.read_float(self.hw + self.offsets["m_dwPunchAngles"])
            self.punch_yaw = self.pm.read_float(self.hw + self.offsets["m_dwPunchAngles"] + 0x4)
        except:
            self.punch_pitch = 0.0
            self.punch_yaw = 0.0
        # Read on-ground flag for bhop
        try:
            self.on_ground = self.pm.read_int(self.hw + self.offsets["m_dwOnGround"])
        except:
            self.on_ground = 0
        # Read weapon ID
        try:
            self.weapon_id = self.pm.read_int(self.hw + self.offsets["m_dwWeaponId"])
        except:
            self.weapon_id = 0
        ent = self.get_entity()
        self.entities_list = self.remove_inactive(self.entities_list_full, ent)
        self.entities_list_full = ent
        

    def write_view_angles(self, yaw, pitch):
        """Write new view angles to game memory (used by aimbot)."""
        self.pm.write_float(self.hw + self.offsets["m_dwViewAngles"], float(pitch))
        self.pm.write_float(self.hw + self.offsets["m_dwViewAngles"] + 0x4, float(yaw))

    def write_force_jump(self, value):
        """Write force jump command (5=press, 4=release)."""
        self.pm.write_int(self.client + self.offsets["m_dwForceJump"], int(value))

    def write_force_attack(self, value):
        """Write force attack command (5=press, 4=release)."""
        self.pm.write_int(self.client + self.offsets["m_dwForceAttack"], int(value))

        
        
        



        
        


    