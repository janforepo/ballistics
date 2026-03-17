
# Nadzvuková (Supersonic): Rychlost střely > 412 m/s (Mach > 1.2)
#
# Transsonická (Transonic): Rychlost střely mezi 274 m/s a 412 m/s (Mach 0.8 - 1.2)
#
# Podzvuková (Subsonic): Rychlost střely < 274 m/s (Mach < 0.8)

import math
import random
import tkinter as tk
from tkinter import ttk

# --- Constants & Presets ---

WEAPON_PRESETS = {
    "---":      {},
    # 9mm FMJ (115-124 gr)
    "glock-17":        {"v0": 360, "m": 0.007451, "r": 0.0045, "C_d": 0.335, "C_d_sup": 0.30, "C_d_trans": 0.45, "C_d_sub": 0.38},
    # .50 AE FMJ (300 gr)
    "Desert Eagle":    {"v0": 475, "m": 0.01944,  "r": 0.00635, "C_d": 0.37,  "C_d_sup": 0.35, "C_d_trans": 0.50, "C_d_sub": 0.42},
    # 9mm FMJ (115-124 gr)
    "Koch MP5":        {"v0": 400, "m": 0.00745,  "r": 0.0045,  "C_d": 0.335, "C_d_sup": 0.30, "C_d_trans": 0.45, "C_d_sub": 0.38},
    # 5.56x45mm M193/M855 FMJ (např. 55-62 gr)
    "M-16":            {"v0": 930, "m": 0.00402,  "r": 0.00278, "C_d": 0.22,  "C_d_sup": 0.20, "C_d_trans": 0.38, "C_d_sub": 0.30},
    # 7.62x39mm FMJ (122-123 gr)
    "AK-47":           {"v0": 715, "m": 0.00797,  "r": 0.00381, "C_d": 0.3,   "C_d_sup": 0.28, "C_d_trans": 0.48, "C_d_sub": 0.40},
    # 7.62x51mm NATO FMJ (147-150 gr)
    "M240":            {"v0": 840, "m": 0.00952,  "r": 0.00381, "C_d": 0.26,  "C_d_sup": 0.25, "C_d_trans": 0.42, "C_d_sub": 0.35},
    # .338 Lapua Magnum (250 gr)
    "AWM":             {"v0": 900, "m": 0.0162,   "r": 0.0043,  "C_d": 0.22,  "C_d_sup": 0.225, "C_d_trans": 0.35, "C_d_sub": 0.28},
    # .50 BMG FMJ (např. 660-750 gr)
    "Barrett M82":     {"v0": 870, "m": 0.04277,  "r": 0.00635, "C_d": 0.25,  "C_d_sup": 0.22, "C_d_trans": 0.38, "C_d_sub": 0.32},
}

DEFAULT_RHO = 1.225  # kg/m³ (air density)
DT = 0.005  # Time step for integration
METERS_PER_PIXEL = 10  # World to screen scaling

# --- Utility Functions ---

def update_green_output_visibility(*args):
    if selected_option.get() == "---":
        # Hide green output widgets
        label_title_green.grid_remove()
        label_range_green.grid_remove()
        label_height_green.grid_remove()
        label_time_green.grid_remove()
        entry_range_air_Three.grid_remove()
        entry_height_air_Three.grid_remove()
        entry_time_air_Three.grid_remove()
    else:
        # Show green output widgets
        label_title_green.grid()
        label_range_green.grid()
        label_height_green.grid()
        label_time_green.grid()
        entry_range_air_Three.grid()
        entry_height_air_Three.grid()
        entry_time_air_Three.grid()

def update_readonly_entry(entry_widget, value):
    entry_widget.config(state="normal")
    entry_widget.delete(0, tk.END)
    entry_widget.insert(0, value)
    entry_widget.config(state="readonly")

def get_value(entry, default, set_if_empty=True):
    try:
        return float(entry.get())
    except ValueError:
        if set_if_empty:
            entry.delete(0, tk.END)
            # Use str(default) to keep all the decimal places
            entry.insert(0, str(default))
        return default

def to_canvas(x, y, canvas_width, canvas_height, x_scale, y_scale):
    cx = x * x_scale
    cy = canvas_height - y * y_scale
    return cx, cy

def clear_all():
    # Clear basic and advanced input fields
    for e in entries_basic + entries_adv:
        e.delete(0, tk.END)

    update_green_output_visibility()

    # Clear output fields
    for e in [
        entry_range_no_air, entry_height_no_air, entry_time_no_air,
        entry_range_air_One, entry_height_air_One, entry_time_air_One,
        entry_range_air_Three, entry_height_air_Three, entry_time_air_Three
    ]:
        e.config(state="normal")
        e.delete(0, tk.END)
        e.config(state="readonly")

    # Clear canvas too (optional, remove if you want to keep trajectories)
    canvas.delete("all")

# --- Simulation Logic ---

def simulate():
    canvas.delete("all")

    # Read selected weapon preset
    weapon_name = selected_option.get()
    preset = WEAPON_PRESETS.get(weapon_name, {})

    # --- Get inputs with fallbacks ---
    v0 = get_value(entry_v0, preset.get("v0", random.uniform(100, 1000)))
    angle_deg = get_value(entry_angle, random.randint(5, 85))
    y0 = get_value(entry_y0, 0)
    g = get_value(entry_g, 9.81)

    m = get_value(entry_m, preset.get("m", random.uniform(0.005, 0.05)))
    r = get_value(entry_r, preset.get("r", random.uniform(0.002, 0.007)))
    A = get_value(entry_A, math.pi * r ** 2)
    rho = get_value(entry_rho, DEFAULT_RHO)
    C_d = get_value(entry_Cd, preset.get("C_d", random.uniform(0.15, 0.5)))  # add safe fallback

    C_d_sup = preset.get("C_d_sup")
    C_d_trans = preset.get("C_d_trans")
    C_d_sub = preset.get("C_d_sub")

    angle_rad = math.radians(angle_deg)
    vx0 = v0 * math.cos(angle_rad)
    vy0 = v0 * math.sin(angle_rad)

    # --- Canvas Setup ---
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()
    WORLD_WIDTH = canvas_width * METERS_PER_PIXEL
    WORLD_HEIGHT = canvas_height * METERS_PER_PIXEL
    x_scale = canvas_width / WORLD_WIDTH
    y_scale = canvas_height / WORLD_HEIGHT

    # --- No Air Resistance (Grey Line) ---
    x, y = 0, y0
    vx, vy = vx0, vy0
    t = 0
    h_max = y0
    x_prev, y_prev = x, y

    t = vy / g
    h_max = vy * t - 0.5 * g * t * t
    t_max = 2 * t
    x_max = vx * t_max

    while y >= 0:
        x += vx * DT
        vy -= g * DT
        y += vy * DT
        # t += DT
        # h_max = max(h_max, y)
        x1, y1 = to_canvas(x_prev, y_prev, canvas_width, canvas_height, x_scale, y_scale)
        x2, y2 = to_canvas(x, y, canvas_width, canvas_height, x_scale, y_scale)
        canvas.create_line(x1, y1, x2, y2, fill="grey")
        x_prev, y_prev = x, y

    R_no_air, T_no_air, H_no_air = x_max, t_max, h_max

    # --- Update Output Entries(No Air Resistance) ---

    update_readonly_entry(entry_range_no_air, f"{R_no_air:.2f}")
    update_readonly_entry(entry_height_no_air, f"{H_no_air:.2f}")
    update_readonly_entry(entry_time_no_air, f"{T_no_air:.2f}")

    # --- With Air Resistance One Cd (Blue Line) ---
    x, y = 0, y0
    vx, vy = vx0, vy0
    t = 0
    h_max = y0
    x_prev, y_prev = x, y

    while y >= 0:
        v = math.sqrt(vx**2 + vy**2)
        F_drag = 0.5 * C_d * rho * A * v**2
        ax = -F_drag * (vx / v) / m
        ay = -g - F_drag * (vy / v) / m

        vx += ax * DT
        vy += ay * DT
        x += vx * DT
        y += vy * DT
        t += DT
        h_max = max(h_max, y)

        x1, y1 = to_canvas(x_prev, y_prev, canvas_width, canvas_height, x_scale, y_scale)
        x2, y2 = to_canvas(x, y, canvas_width, canvas_height, x_scale, y_scale)
        canvas.create_line(x1, y1, x2, y2, fill="blue")
        x_prev, y_prev = x, y

    R_air_One, T_air_One, H_air_One = x, t, h_max

    # --- Update Output Entries (With Air Resistance One C_d) ---

    update_readonly_entry(entry_range_air_One, f"{R_air_One:.2f}")
    update_readonly_entry(entry_height_air_One, f"{H_air_One:.2f}")
    update_readonly_entry(entry_time_air_One, f"{T_air_One:.2f}")

    if weapon_name != "---":
        x, y = 0, y0
        vx, vy = vx0, vy0
        t = 0
        h_max = y0
        x_prev, y_prev = x, y

        while y >= 0:
            # 1. ALWAYS calculate current velocity first
            v = math.sqrt(vx ** 2 + vy ** 2)

            # 2. Assign the coefficient safely
            if v > 412:
                tC_d = C_d_sup
            elif 274 <= v <= 412:
                tC_d = C_d_trans
            else:
                tC_d = C_d_sub

            # 3. Calculate physics
            F_drag = 0.5 * tC_d * rho * A * (v ** 2)

            # Prevent division by zero if it stops completely
            if v > 0:
                ax = -F_drag * (vx / v) / m
                ay = -g - F_drag * (vy / v) / m
            else:
                ax, ay = 0, -g

            # 4. Integrate
            vx += ax * DT
            vy += ay * DT
            x += vx * DT
            y += vy * DT
            t += DT
            h_max = max(h_max, y)

            # 5. Draw
            x1, y1 = to_canvas(x_prev, y_prev, canvas_width, canvas_height, x_scale, y_scale)
            x2, y2 = to_canvas(x, y, canvas_width, canvas_height, x_scale, y_scale)
            canvas.create_line(x1, y1, x2, y2, fill="green")
            x_prev, y_prev = x, y

            print(f"Y: {y}")

        R_air_Three, T_air_Three, H_air_Three = x, t, h_max

        # --- Update Output Entries (With Air Resistance Three C_d) ---

        update_readonly_entry(entry_range_air_Three, f"{R_air_Three:.2f}")
        update_readonly_entry(entry_height_air_Three, f"{H_air_Three:.2f}")
        update_readonly_entry(entry_time_air_Three, f"{T_air_Three:.2f}")




# --- GUI Setup ---

root = tk.Tk()
root.title("Ballistic Trajectory Simulator")
root.minsize(600, 600)

canvas = tk.Canvas(root, bg="white")
canvas.pack(fill=tk.BOTH, expand=True)

input_frame = tk.Frame(root)
input_frame.pack(pady=10)

# --- Input Fields: Basic Physics ---
labels_basic = ["v0 (m/s)", "Angle (°)", "y0 (m)", "g (m/s²)"]
entries_basic = []
for i, text in enumerate(labels_basic):
    tk.Label(input_frame, text=text).grid(row=0, column=i)
    e = tk.Entry(input_frame, width=10)
    e.grid(row=1, column=i, padx=5)
    entries_basic.append(e)

entry_v0, entry_angle, entry_y0, entry_g = entries_basic

# --- Weapon Dropdown ---
tk.Label(input_frame, text="Choose a weapon").grid(row=0, column=5)
selected_option = tk.StringVar()
dropdown = ttk.Combobox(input_frame, textvariable=selected_option, state='readonly')
dropdown['values'] = list(WEAPON_PRESETS.keys())
dropdown.current(0)
dropdown.grid(row=1, column=5)

# --- Input Fields: Advanced Parameters ---
labels_adv = ["m (kg)", "r (m)", "A (m²)", "C_d", "ρ (kg/m³)"]
entries_adv = []
for i, text in enumerate(labels_adv):
    tk.Label(input_frame, text=text).grid(row=2, column=i)
    e = tk.Entry(input_frame, width=10)
    e.grid(row=3, column=i, padx=5)
    entries_adv.append(e)

entry_m, entry_r, entry_A, entry_Cd, entry_rho = entries_adv

# --- Output: Without Air Resistance (Grey) ---
tk.Label(input_frame, text="Without Air Resistance", fg="grey").grid(row=4, column=0, columnspan=2)
tk.Label(input_frame, text="Range R (m)").grid(row=5, column=0)
tk.Label(input_frame, text="Max Height H (m)").grid(row=5, column=1)
tk.Label(input_frame, text="Time T (s)").grid(row=5, column=2)

entry_range_no_air = tk.Entry(input_frame, width=10, state="readonly")
entry_height_no_air = tk.Entry(input_frame, width=10, state="readonly")
entry_time_no_air = tk.Entry(input_frame, width=10, state="readonly")
entry_range_no_air.grid(row=6, column=0, padx=5)
entry_height_no_air.grid(row=6, column=1, padx=5)
entry_time_no_air.grid(row=6, column=2, padx=5)

# --- Output: With Air Resistance One C_d (Blue) ---
tk.Label(input_frame, text="With Air Resistance", fg="blue").grid(row=7, column=0, columnspan=2)
tk.Label(input_frame, text="Range R (m)").grid(row=8, column=0)
tk.Label(input_frame, text="Max Height H (m)").grid(row=8, column=1)
tk.Label(input_frame, text="Time T (s)").grid(row=8, column=2)

entry_range_air_One = tk.Entry(input_frame, width=10, state="readonly")
entry_height_air_One = tk.Entry(input_frame, width=10, state="readonly")
entry_time_air_One = tk.Entry(input_frame, width=10, state="readonly")
entry_range_air_One.grid(row=9, column=0, padx=5)
entry_height_air_One.grid(row=9, column=1, padx=5)
entry_time_air_One.grid(row=9, column=2, padx=5)

    # --- Output: With Air Resistance Three C_d (Green) ---

# 1. Create the labels and entries
label_title_green = tk.Label(input_frame, text="With Air Resistance (More Accurate)", fg="green")
label_range_green = tk.Label(input_frame, text="Range R (m)")
label_height_green = tk.Label(input_frame, text="Max Height H (m)")
label_time_green = tk.Label(input_frame, text="Time T (s)")

entry_range_air_Three = tk.Entry(input_frame, width=10, state="readonly")
entry_height_air_Three = tk.Entry(input_frame, width=10, state="readonly")
entry_time_air_Three = tk.Entry(input_frame, width=10, state="readonly")

# 2. Place them using .grid() (don't worry, we'll hide them later if needed)
label_title_green.grid(row=10, column=0, columnspan=2)
label_range_green.grid(row=11, column=0)
label_height_green.grid(row=11, column=1)
label_time_green.grid(row=11, column=2)

entry_range_air_Three.grid(row=12, column=0, padx=5)
entry_height_air_Three.grid(row=12, column=1, padx=5)
entry_time_air_Three.grid(row=12, column=2, padx=5)

def on_weapon_selected(event):
    clear_all()  # Clear everything first
    update_green_output_visibility()  # Keep your visibility logic

dropdown.bind("<<ComboboxSelected>>", on_weapon_selected)
update_green_output_visibility()

tk.Button(root, text="Clear All", command=clear_all).pack(pady=5)


# --- Simulate Button ---
tk.Button(root, text="Simulate Trajectories", command=simulate).pack(pady=10)

root.mainloop()




# todo Fix y0 error max_t may be wrong - check
# todo Print values to the boxes ere the simulation is triggered (on choosing of dropdown)
# todo Must update r before simulate, if changed manually may cause trouble
# todo Add input box variable for meters/px - make it adjustable
