import pygame
import sys
import time
import json
import os
import random
import math
from audio import AudioManager
from ui import Button, Checkbox, JudgmentText, init_font, Slider, Dropdown

# --- PYINSTALLER PATH FIX ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- GLOBAL CONSTANTS ---
CONFIG_FILE = "settings.json"

# OFFICIAL ARCADE TIMING WINDOWS (in seconds)
WINDOW_PERFECT = 0.025  # 25ms
WINDOW_OK      = 0.075  # 75ms
WINDOW_BAD     = 0.108  # 108ms

# UI and Visual Colors
COLOR_BG = (20, 20, 20)
COLOR_BAR = (10, 10, 10)
COLOR_HIT_LINE = (255, 255, 255)
COLOR_GRID = (60, 60, 60)
COLOR_DON = (235, 69, 44) 
COLOR_KA = (67, 142, 172)
COLOR_EMPTY_SLOT = (40, 40, 40)

# Accuracy Feedback Colors
COL_JUDGE_PERFECT = (255, 220, 50) 
COL_JUDGE_EARLY   = (50, 150, 255) 
COL_JUDGE_LATE    = (255, 80, 80)  
COL_JUDGE_BAD     = (180, 80, 255) 
COL_JUDGE_MISS    = (120, 120, 120)

# Scroll Speed Options (Multipliers)
SPEED_OPTIONS = [
    {"name": "Speed: 1.0x", "val": 1.0},
    {"name": "Speed: 1.1x", "val": 1.1},
    {"name": "Speed: 1.2x", "val": 1.2},
    {"name": "Speed: 1.3x", "val": 1.3},
    {"name": "Speed: 1.4x", "val": 1.4},
    {"name": "Speed: 1.5x", "val": 1.5},
    {"name": "Speed: 2.0x", "val": 2.0},
    {"name": "Speed: 2.5x", "val": 2.5},
    {"name": "Speed: 3.0x", "val": 3.0},
    {"name": "Speed: 3.5x", "val": 3.5},
    {"name": "Speed: 4.0x", "val": 4.0},
]

# Preset Rudiments Data
PRESETS = [
    {"name": "Don 1/8 Stream [● ●]", "data": [1, 0, 1, 0] * 8},
    {"name": "Ka 1/8 Stream [○ ○]", "data": [2, 0, 2, 0] * 8},
    {"name": "Don-Ka 1/16 Alt [●○●○]", "data": [1, 2, 1, 2] * 8},
    {"name": "Triplets DON [●●●]", "data": [1, 1, 1, 0] * 8},
    {"name": "Triplets KA [○○○]", "data": [2, 2, 2, 0] * 8},
    {"name": "DDK Triplet [●●○]", "data": [1, 1, 2, 0] * 8},
    {"name": "KKD Triplet [○○●]", "data": [2, 2, 1, 0] * 8},
    {"name": "Don 1/16 Stream [●●●●]", "data": [1] * 32},
    {"name": "Ka 1/16 Stream [○○○○]", "data": [2] * 32},
]

class PatternSequencer:
    """Handles the 32-step pattern grid logic and rendering."""
    def __init__(self, x, y, width, slots=32):
        self.x, self.y, self.width, self.slots = x, y, width, slots
        self.spacing = 4
        self.box_size = (self.width - ((self.slots - 1) * self.spacing)) / self.slots
        self.pattern = [0] * slots 
        self.hovered_slot = -1

    def update_layout(self, x, y, width):
        self.x, self.y, self.width = x, y, width
        raw_size = (self.width - ((self.slots - 1) * self.spacing)) / self.slots
        self.box_size = max(15, min(40, raw_size))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            rel_x = mx - self.x
            total_w = (self.box_size + self.spacing) * self.slots
            if 0 <= (my - self.y) <= self.box_size and 0 <= rel_x <= total_w:
                self.hovered_slot = int(rel_x // (self.box_size + self.spacing))
                if self.hovered_slot >= self.slots: self.hovered_slot = -1
            else:
                self.hovered_slot = -1
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered_slot != -1 and 0 <= self.hovered_slot < self.slots:
                self.pattern[self.hovered_slot] = (self.pattern[self.hovered_slot] + 1) % 3
                return True
        return False

    def draw(self, screen, current_step_idx=-1):
        for i in range(self.slots):
            bx = self.x + i * (self.box_size + self.spacing)
            rect = pygame.Rect(bx, self.y, self.box_size, self.box_size)
            val = self.pattern[i]
            col = COLOR_EMPTY_SLOT
            if val == 1: col = COLOR_DON
            elif val == 2: col = COLOR_KA
            if i == current_step_idx: pygame.draw.rect(screen, (255, 255, 0), rect.inflate(4, 4), 2)
            pygame.draw.rect(screen, col, rect, border_radius=3)
            pygame.draw.rect(screen, (100, 100, 100), rect, 1, border_radius=3)
            if i > 0 and i % 16 == 0:
                sep_x = bx - (self.spacing / 2)
                pygame.draw.line(screen, (255, 255, 255), (sep_x, self.y - 10), (sep_x, self.y + self.box_size + 10), 2)
            elif i % 4 == 0: pygame.draw.circle(screen, (150, 150, 150), (bx + self.box_size/2, self.y - 6), 2)

    def clear(self): self.pattern = [0] * self.slots
    def randomize(self): self.pattern = [random.choice([0, 0, 1, 2]) for _ in range(self.slots)]
    def get_pattern_data(self): return list(self.pattern)
    def set_pattern_data(self, data):
        if len(data) == self.slots: self.pattern = list(data)
        else: self.pattern = (list(data) + [0]*self.slots)[:self.slots]

def load_settings():
    """Load user settings from JSON or return defaults."""
    defaults = {
        "bpm": 100, "hs_multiplier": 1.0, "vol_don": 0.8, "vol_ka": 0.8, "vol_metro": 0.5, 
        "is_game_mode": False, "offset": 0.0, "scale_bpm": True,
        "auto_randomize": False, "custom_pattern": [0] * 32,
        "binds": {"don_l": pygame.K_f, "don_r": pygame.K_j, "ka_l": pygame.K_d, "ka_r": pygame.K_k}
    }
    if not os.path.exists(CONFIG_FILE): return defaults
    try:
        with open(CONFIG_FILE, 'r') as f:
            saved = json.load(f)
            if "binds" in saved: defaults["binds"].update(saved["binds"])
            saved.pop("binds", None)
            defaults.update(saved)
            return defaults
    except: return defaults

def save_settings(data):
    """Persist user settings to a JSON file."""
    try:
        with open(CONFIG_FILE, 'w') as f: json.dump(data, f, indent=4)
    except: pass

def get_refresh_rate():
    """Attempt to detect monitor refresh rate. Defaults to 240 if detection fails."""
    try:
        # We try the standard Pygame 2.x detection
        if hasattr(pygame.display, 'get_current_refresh_rate'):
            rr = pygame.display.get_current_refresh_rate()
            if rr > 0: return rr
    except: pass
    return 240 # Increased default fallback to ensure high-end monitors aren't capped

def main():
    pygame.init()
    init_font()
    
    # --- LOAD CUSTOM ICON USING RESOURCE_PATH ---
    icon_path = resource_path(os.path.join("assets", "icon.png"))
    if os.path.exists(icon_path):
        try:
            icon_img = pygame.image.load(icon_path)
            pygame.display.set_icon(icon_img)
        except: pass
            
    font_ui = pygame.font.SysFont("Arial", 18, bold=True)
    font_bpm = pygame.font.SysFont("Arial", 40, bold=True)
    font_stats = pygame.font.SysFont("Consolas", 28, bold=True) 
    font_combo = pygame.font.SysFont("Arial", 64, bold=True)
    
    W, H = 1920, 1080
    screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)
    pygame.display.set_caption("U.B. Taiko Pattern Trainer")
    
    refresh_rate = get_refresh_rate()
    target_fps = max(60, refresh_rate) 
    clock = pygame.time.Clock()
    audio = AudioManager()
    settings = load_settings()

    game_state = {
        "bpm": 100, # Fixed: Always start at 100 BPM
        "hs_multiplier": settings.get("hs_multiplier", 1.0),
        "scale_bpm": settings.get("scale_bpm", True),
        "is_game_mode": settings.get("is_game_mode", False),
        "metronome_active": False,
        "demo_mode": False,
        "offset": settings.get("offset", 0.0),
        "auto_randomize": False, # Fixed: Always start at OFF
        "binds": settings["binds"],
        "waiting_for_key": None,
        "undo_stack": None,
        "combo": 0,
        "max_combo": 0,
        "hit_glow_time": 0,
        "hit_glow_col": (255, 255, 255),
        "current_seq_idx": -1
    }
    
    start_time = 0; game_session_start = 0 
    beat_count = 0; sub_beat_count = 0 
    visual_notes = []; target_notes = []; current_judgment = None 
    last_beat_time = 0
    hit_flash_timers = {"don": 0, "ka": 0} 
    game_stats = {"good": 0, "early": 0, "late": 0, "bad": 0, "miss": 0}
    
    vols = { "don": settings["vol_don"], "ka": settings["vol_ka"], "metro": settings["vol_metro"] }
    for k, v in vols.items(): audio.set_volume(k, v)
    
    sequencer = PatternSequencer(50, H - 60, W - 100, slots=32)
    sequencer.set_pattern_data(settings.get("custom_pattern", [0]*32))

    fps_display = 0; last_fps_update = 0

    # --- UI CALLBACKS ---
    def toggle_gamemode():
        game_state["is_game_mode"] = not game_state["is_game_mode"]
        btn_gamemode.text_override = f"Mode: {'GAME' if game_state['is_game_mode'] else 'VISUALIZER'}"
        game_state["metronome_active"] = False; target_notes.clear(); visual_notes.clear(); game_state["combo"] = 0
    
    def reset_game_state(delay_sec=0):
        nonlocal start_time, game_session_start, beat_count, sub_beat_count, current_judgment, last_beat_time
        game_state["metronome_active"] = True
        game_state["current_seq_idx"] = -1
        
        start_time = time.perf_counter() + delay_sec
        game_session_start = time.perf_counter()
        
        beat_count = 0
        sub_beat_count = 0
            
        visual_notes.clear(); target_notes.clear()
        current_judgment = None
        game_stats.update({"good": 0, "early": 0, "late": 0, "bad": 0, "miss": 0})
        game_state["combo"] = 0
        last_beat_time = 0

    def toggle_demo():
        game_state["demo_mode"] = not game_state["demo_mode"]
        btn_demo.text_override = f"Demo: {'ON' if game_state['demo_mode'] else 'OFF'}"
        if game_state["demo_mode"]: reset_game_state()
        else: game_state["metronome_active"] = False

    def toggle_auto_random():
        game_state["auto_randomize"] = not game_state["auto_randomize"]
        btn_auto_rand.text_override = f"Auto-Random: {'ON' if game_state['auto_randomize'] else 'OFF'}"
    
    def apply_preset(preset):
        game_state["undo_stack"] = sequencer.get_pattern_data()
        sequencer.set_pattern_data(preset["data"])
        dropdown_presets.main_btn.text_override = f"Preset: {preset['name']}"
        if game_state["metronome_active"]: reset_game_state(delay_sec=3.0)

    def apply_hs(option):
        game_state["hs_multiplier"] = option["val"]
        dropdown_hs.main_btn.text_override = f"{option['name']}"
        
    def change_vol(target, amount):
        nonlocal vols; vols[target] = max(0.0, min(1.0, vols[target] + amount))
        audio.set_volume(target, vols[target])
        
    def reset_offset():
        game_state["offset"] = 0.0; sld_offset.val = 0.0
        
    def start_binding(bind_id): game_state["waiting_for_key"] = bind_id
    
    def safe_clear():
        game_state["undo_stack"] = sequencer.get_pattern_data(); sequencer.clear()
        
    def undo_clear():
        if game_state["undo_stack"]: sequencer.set_pattern_data(game_state["undo_stack"])

    # --- UI SETUP ---
    vol_rows = []
    for key, label in [("don", "Don Volume"), ("ka", "Ka Volume"), ("metro", "Metronome")]:
        btn_minus = Button(0, 0, 25, 25, "-", lambda k=key: change_vol(k, -0.05))
        btn_plus = Button(0, 0, 25, 25, "+", lambda k=key: change_vol(k, 0.05))
        vol_rows.append({ "key": key, "label": label, "minus": btn_minus, "plus": btn_plus })

    chk_scale_bpm = Checkbox(0, 0, 24, "Scale BPM to Scroll", game_state["scale_bpm"], lambda v: game_state.update({"scale_bpm": v}))
    
    btn_gamemode = Button(0, 0, 160, 35, f"Mode: {'GAME' if game_state['is_game_mode'] else 'VISUALIZER'}", toggle_gamemode)
    btn_reset_off = Button(0, 0, 60, 25, "Reset", reset_offset)
    dropdown_hs = Dropdown(0, 0, 180, 35, f"Speed: {game_state['hs_multiplier']}x", SPEED_OPTIONS, apply_hs)
    sld_bpm = Slider(0, 0, 300, 40, 400, game_state["bpm"], "BPM", lambda v: game_state.update({"bpm": v}))
    sld_offset = Slider(0, 0, 230, -0.1, 0.1, game_state["offset"], "Global Offset", lambda v: game_state.update({"offset": v}))

    bind_buttons = {}
    bind_configs = [("ka_l", "Left KA"), ("don_l", "Left DON"), ("don_r", "Right DON"), ("ka_r", "Right KA")]
    for b_id, label in bind_configs:
        bind_buttons[b_id] = Button(0, 0, 80, 25, "", lambda b=b_id: start_binding(b))

    btn_clear = Button(0, 0, 120, 35, "Clear Pattern", safe_clear)
    btn_undo = Button(0, 0, 120, 35, "Undo Clear", undo_clear)
    btn_random = Button(0, 0, 120, 35, "Randomize", sequencer.randomize)
    btn_auto_rand = Button(0, 0, 170, 35, f"Auto-Random: OFF", toggle_auto_random)
    btn_demo = Button(0, 0, 120, 35, f"Demo: OFF", toggle_demo)
    dropdown_presets = Dropdown(0, 0, 240, 35, "Select Preset", PRESETS, apply_preset)

    ui_common = [chk_scale_bpm, btn_gamemode, btn_reset_off]
    ui_common.extend(bind_buttons.values())
    for row in vol_rows: ui_common.extend([row["minus"], row["plus"]])
    ui_game_only = [btn_clear, btn_undo, btn_random, btn_auto_rand, btn_demo]

    def try_hit_target(input_type, hit_time, is_auto=False):
        nonlocal current_judgment
        adj_hit = hit_time - game_state["offset"]
        best_note = None; min_diff = 1000
        candidates = [n for n in target_notes if not n.get('hit', False) and n['type'] == input_type]
        for note in candidates:
            calc_diff = abs(note['time'] - adj_hit)
            if calc_diff < min_diff: min_diff = calc_diff; best_note = note
        
        hit_window = WINDOW_PERFECT if is_auto else WINDOW_BAD
        if best_note and min_diff <= hit_window:
            best_note['hit'] = True 
            real_diff = best_note['time'] - adj_hit
            game_state["hit_glow_time"] = hit_time
            game_state["hit_glow_col"] = COLOR_DON if input_type == 'DON' else COLOR_KA
            if min_diff <= WINDOW_PERFECT or is_auto: 
                current_judgment = JudgmentText("GOOD!", COL_JUDGE_PERFECT); game_stats["good"] += 1; game_state["combo"] += 1
            elif min_diff <= WINDOW_OK:
                if real_diff < 0: current_judgment = JudgmentText("LATE", COL_JUDGE_LATE); game_stats["late"] += 1
                else: current_judgment = JudgmentText("EARLY", COL_JUDGE_EARLY); game_stats["early"] += 1
                game_state["combo"] += 1
            else: 
                current_judgment = JudgmentText("BAD", COL_JUDGE_BAD); game_stats["bad"] += 1; game_state["combo"] = 0
            game_state["max_combo"] = max(game_state["combo"], game_state["max_combo"])
            return True
        return False

    while True:
        current_time = time.perf_counter()
        W, H = screen.get_size()
        screen.fill(COLOR_BG)
        
        BAR_Y, BAR_H, NOTE_R = 120, 200, 42 
        HIT_X = W // 4 if game_state["is_game_mode"] else W - 300
        center_y = BAR_Y + (BAR_H // 2) 
        
        LEFT_MARGIN, SPACING_Y, BTN_GAP = 50, 35, 12
        y_calc = H - 530 
        
        # Calculate Effective Scroll Speed
        base_scroll = 500
        if game_state["scale_bpm"]: base_scroll = (game_state["bpm"] / 120.0) * 500
        eff_scroll = base_scroll * game_state["hs_multiplier"]

        # UI Positioning
        for row in vol_rows:
            row["minus"].rect.topleft = (LEFT_MARGIN + 160, y_calc)
            row["plus"].rect.topleft = (row["minus"].rect.right + 5, y_calc)
            y_calc += SPACING_Y
        
        y_calc += 10
        sld_bpm.set_pos(LEFT_MARGIN, y_calc + 30); y_calc += 55
        sld_offset.set_pos(LEFT_MARGIN, y_calc + 30)
        btn_reset_off.rect.topleft = (sld_offset.rect.right + 10, sld_offset.rect.y - 5)
        y_calc += 55
        chk_scale_bpm.rect.topleft = (LEFT_MARGIN, y_calc); y_calc += SPACING_Y
        dropdown_hs.main_btn.rect.topleft = (LEFT_MARGIN, y_calc); y_calc += 45
        for i, b in enumerate(dropdown_hs.option_buttons):
            b.rect.topleft = (dropdown_hs.main_btn.rect.x, dropdown_hs.main_btn.rect.y - (len(dropdown_hs.option_buttons) - i) * b.rect.h)
        btn_gamemode.rect.topleft = (LEFT_MARGIN, y_calc)

        if game_state["is_game_mode"]:
            y_row = H - 110 
            btn_clear.rect.topleft = (LEFT_MARGIN, y_row)
            btn_undo.rect.topleft = (btn_clear.rect.right + BTN_GAP, y_row)
            btn_random.rect.topleft = (btn_undo.rect.right + BTN_GAP, y_row)
            btn_auto_rand.rect.topleft = (btn_random.rect.right + BTN_GAP, y_row)
            dropdown_presets.main_btn.rect.topleft = (btn_auto_rand.rect.right + BTN_GAP, y_row)
            btn_demo.rect.topleft = (dropdown_presets.main_btn.rect.right + BTN_GAP, y_row)
            for i, b in enumerate(dropdown_presets.option_buttons):
                b.rect.topleft = (dropdown_presets.main_btn.rect.x, dropdown_presets.main_btn.rect.y - (len(dropdown_presets.option_buttons) - i) * b.rect.h)
            sequencer.update_layout(50, H - 50, W - 100)

        bx, by = W - 320, H - 530
        for b_id, label in bind_configs:
            btn = bind_buttons[b_id]; btn.rect.topleft = (bx + 110, by)
            btn.text_override = "???" if game_state["waiting_for_key"] == b_id else pygame.key.name(game_state["binds"][b_id]).upper()
            by += SPACING_Y

        # --- EVENT HANDLING ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_settings({"bpm": game_state["bpm"], "hs_multiplier": game_state["hs_multiplier"], "scale_bpm": game_state["scale_bpm"], "vol_don": vols["don"], "vol_ka": vols["ka"], "vol_metro": vols["metro"], "is_game_mode": game_state["is_game_mode"], "offset": game_state["offset"], "auto_randomize": game_state["auto_randomize"], "custom_pattern": sequencer.get_pattern_data(), "binds": game_state["binds"]})
                pygame.quit(); sys.exit()
            
            if game_state["waiting_for_key"] and event.type == pygame.KEYDOWN:
                if event.key != pygame.K_ESCAPE: game_state["binds"][game_state["waiting_for_key"]] = event.key
                game_state["waiting_for_key"] = None; continue

            if game_state["is_game_mode"] and dropdown_presets.handle_event(event): continue
            if dropdown_hs.handle_event(event): continue
            if sld_bpm.handle_event(event): continue
            if sld_offset.handle_event(event): continue
            
            ui_handled = False
            for el in ui_common:
                if el.handle_event(event): ui_handled = True
            
            if game_state["is_game_mode"]:
                for el in ui_game_only:
                    if el.handle_event(event): ui_handled = True
                if not ui_handled and sequencer.handle_event(event): ui_handled = True
            
            if not ui_handled and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: pygame.event.post(pygame.event.Event(pygame.QUIT))
                if event.key == pygame.K_F11:
                    is_full = screen.get_flags() & pygame.FULLSCREEN
                    screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN) if not is_full else pygame.display.set_mode((1920, 1080), pygame.RESIZABLE)
                
                # Re-implemented BPM arrows with 5 BPM step
                if event.key == pygame.K_RIGHT:
                    game_state["bpm"] = min(400, game_state["bpm"] + 5)
                    sld_bpm.val = game_state["bpm"]
                    sld_bpm.update_handle_pos()
                if event.key == pygame.K_LEFT:
                    game_state["bpm"] = max(40, game_state["bpm"] - 5)
                    sld_bpm.val = game_state["bpm"]
                    sld_bpm.update_handle_pos()
                
                if event.key == pygame.K_SPACE:
                    game_state["metronome_active"] = not game_state["metronome_active"]
                    if game_state["metronome_active"]: reset_game_state()
                
                is_don = event.key in [game_state["binds"]["don_l"], game_state["binds"]["don_r"]]
                is_ka = event.key in [game_state["binds"]["ka_l"], game_state["binds"]["ka_r"]]
                if not game_state["demo_mode"] and (is_don or is_ka):
                    audio.play("don" if is_don else "ka")
                    hit_flash_timers["don" if is_don else "ka"] = current_time
                    if game_state["metronome_active"]:
                        if game_state["is_game_mode"]: try_hit_target('DON' if is_don else 'KA', current_time)
                        else: visual_notes.append(('DON' if is_don else 'KA', current_time))

        # --- UPDATE LOGIC ---
        if game_state["metronome_active"]:
            b_int = 60.0 / game_state["bpm"]
            sb_int = b_int / 4; elapsed = current_time - start_time
            valid_elapsed = max(0, elapsed)
            
            if elapsed >= 0:
                if int(valid_elapsed / b_int) > beat_count: 
                    beat_count = int(valid_elapsed / b_int); audio.play("metro_tick")
                new_idx = int(valid_elapsed / sb_int) % 32
                
                # Robust Loop Detection for Auto-Randomizer
                if game_state["auto_randomize"] and new_idx == 0 and game_state["current_seq_idx"] == 31:
                    sequencer.randomize()
                    
                game_state["current_seq_idx"] = new_idx
                if game_state["is_game_mode"] and int(valid_elapsed / sb_int) > sub_beat_count:
                    sub_beat_count = int(valid_elapsed / sb_int)
                    lookahead = int(((W - HIT_X + 100) / eff_scroll) / sb_int)
                    future_idx = (sub_beat_count + lookahead) % 32
                    if sequencer.pattern[future_idx] > 0:
                        target_notes.append({'type': 'DON' if sequencer.pattern[future_idx] == 1 else 'KA', 'time': start_time + ((sub_beat_count + lookahead) * sb_int), 'hit': False})

            if game_state["demo_mode"]:
                for n in target_notes:
                    if not n['hit'] and current_time >= n['time'] + game_state["offset"]:
                        audio.play("don" if n['type'] == 'DON' else "ka"); hit_flash_timers["don" if n['type'] == 'DON' else "ka"] = current_time
                        try_hit_target(n['type'], current_time, is_auto=True)

        # --- RENDERING ---
        pygame.draw.rect(screen, COLOR_BAR, (0, BAR_Y, W, BAR_H))
        
        if game_state["metronome_active"]:
            b_int = 60.0 / game_state["bpm"]; rel_start = current_time - start_time
            start_idx = int((-HIT_X / eff_scroll + rel_start) / b_int) - 1
            end_idx = int(((W - HIT_X) / eff_scroll + rel_start) / b_int) + 1
            for i in range(start_idx, end_idx):
                lx = HIT_X + (start_time + i * b_int - current_time) * eff_scroll
                if 0 < lx < W:
                    col = (200, 200, 200) if i % 4 == 0 else (80, 80, 80)
                    pygame.draw.line(screen, col, (lx, BAR_Y), (lx, BAR_Y + BAR_H), 3 if i % 4 == 0 else 1)

        # Glow and Feedback
        glow_elapsed = current_time - game_state["hit_glow_time"]
        if glow_elapsed < 0.15:
            alpha = int(180 * (1.0 - (glow_elapsed / 0.15)))
            s = pygame.Surface((NOTE_R*5, NOTE_R*5), pygame.SRCALPHA)
            pygame.draw.circle(s, (*game_state["hit_glow_col"], alpha), (NOTE_R*2.5, NOTE_R*2.5), NOTE_R * 1.8)
            screen.blit(s, (HIT_X - NOTE_R*2.5, center_y - NOTE_R*2.5))

        pygame.draw.circle(screen, (200, 200, 200), (HIT_X, center_y), NOTE_R, 4)
        for t, c in [("don", COLOR_DON), ("ka", COLOR_KA)]:
            flash = current_time - hit_flash_timers[t]
            if flash < 0.1:
                s = pygame.Surface((NOTE_R*2, NOTE_R*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*c, int(150 * (1.0 - flash/0.1))), (NOTE_R, NOTE_R), NOTE_R)
                screen.blit(s, (HIT_X - NOTE_R, center_y - NOTE_R))

        pygame.draw.line(screen, COLOR_HIT_LINE, (HIT_X, BAR_Y - 20), (HIT_X, BAR_Y + BAR_H + 20), 4 if not game_state["is_game_mode"] else 2)

        if game_state["metronome_active"]:
            if game_state["is_game_mode"]:
                missed = [n for n in target_notes if n['time'] < current_time - WINDOW_BAD and not n['hit']]
                if missed:
                    current_judgment = JudgmentText("MISS", COL_JUDGE_MISS); game_stats["miss"] += len(missed); game_state["combo"] = 0
                    for m in missed: target_notes.remove(m)
                for note in target_notes:
                    if not note.get('hit'):
                        nx = HIT_X + (note['time'] - current_time) * eff_scroll
                        if -100 < nx < W + 100:
                            pygame.draw.circle(screen, (255,255,255), (int(nx), center_y), NOTE_R)
                            pygame.draw.circle(screen, COLOR_DON if note['type'] == 'DON' else COLOR_KA, (int(nx), center_y), int(NOTE_R * 0.9))
                if game_state["combo"] >= 10:
                    c_surf = font_combo.render(f"{game_state['combo']}", True, (255, 255, 255))
                    screen.blit(c_surf, (HIT_X - c_surf.get_width()//2, BAR_Y - 80))
            else:
                visual_notes = [n for n in visual_notes if (HIT_X - (current_time - n[1]) * eff_scroll) > -100]
                for n_type, n_time in visual_notes:
                    nx = HIT_X - (current_time - n_time) * eff_scroll
                    if -100 < nx < W + 50:
                        pygame.draw.circle(screen, (255,255,255), (int(nx), center_y), NOTE_R)
                        pygame.draw.circle(screen, COLOR_DON if n_type == 'DON' else COLOR_KA, (int(nx), center_y), int(NOTE_R * 0.9))
            if current_judgment: current_judgment.draw(screen, HIT_X, center_y)
        else:
            txt = font_bpm.render("PRESS SPACE TO START", True, (80, 80, 80)); screen.blit(txt, txt.get_rect(center=(W//2, center_y)))
            if game_state["is_game_mode"]:
                total = sum(game_stats.values())
                if total > 10:
                    tip = ""
                    if game_stats["early"] > (game_stats["good"] + game_stats["late"]) * 0.4: tip = "TIP: Hitting EARLY! Increase Offset or relax."
                    elif game_stats["late"] > (game_stats["good"] + game_stats["early"]) * 0.4: tip = "TIP: Hitting LATE! Decrease Offset or anticipate."
                    elif game_stats["miss"] > total * 0.3: tip = "TIP: Too many MISSes? Try slowing down BPM."
                    if tip:
                        ts = font_ui.render(tip, True, (255, 255, 0)); screen.blit(ts, ts.get_rect(center=(W//2, center_y + 160)))

        # DRAW UI
        cur_y = H - 530
        for row in vol_rows:
            screen.blit(font_ui.render(f"{row['label']}: {int(vols[row['key']] * 100)}%", True, (255,255,255)), (LEFT_MARGIN, cur_y + 2))
            row["minus"].draw(screen); row["plus"].draw(screen); cur_y += SPACING_Y
        sld_bpm.draw(screen); sld_offset.draw(screen); btn_reset_off.draw(screen)
        chk_scale_bpm.draw(screen); dropdown_hs.draw(screen); btn_gamemode.draw(screen)

        if game_state["is_game_mode"]:
            for el in ui_game_only: el.draw(screen)
            dropdown_presets.draw(screen); sequencer.draw(screen, game_state["current_seq_idx"] if game_state["metronome_active"] else -1)
            stats_x, lh = HIT_X - 280, 28; sy = center_y - (3.5 * lh)
            el_s = int(max(0, time.perf_counter() - game_session_start)) if game_state["metronome_active"] else 0
            screen.blit(font_stats.render(f"Time: {el_s // 60:02}:{el_s % 60:02}", True, (255, 255, 255)), (stats_x, sy))
            for i, (l, v, c) in enumerate([("GOOD ", game_stats['good'], COL_JUDGE_PERFECT), ("EARLY", game_stats['early'], COL_JUDGE_EARLY), ("LATE ", game_stats['late'], COL_JUDGE_LATE), ("BAD  ", game_stats['bad'], COL_JUDGE_BAD), ("MISS ", game_stats['miss'], COL_JUDGE_MISS)]):
                screen.blit(font_stats.render(f"{l}: {v:02d}", True, c), (stats_x, sy + (i+1)*lh))

        bx = W - 320; by = H - 530
        for b_id, label in bind_configs:
            screen.blit(font_ui.render(f"{label}:", True, (200, 200, 200)), (bx, by + 2))
            bind_buttons[b_id].draw(screen); by += SPACING_Y

        if current_time - last_fps_update > 5.0: fps_display = int(clock.get_fps()); last_fps_update = current_time
        screen.blit(font_bpm.render(f"BPM: {int(game_state['bpm'])}", True, (255, 255, 255)), (W - 220, 50))
        screen.blit(font_ui.render(f"FPS: {fps_display} / {target_fps}", True, (150, 150, 150)), (W - 220, 95))
        pygame.display.flip(); clock.tick(target_fps)

if __name__ == "__main__": main()