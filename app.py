import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.set_page_config(layout="wide")

# --- ACADEMIC TITLE & DOCUMENTATION ---
st.title("Series Ag-Rover Run Time Simulation")
st.write(
    "A custom predictive sizing model developed by electrical and mechanical engineering students "
    "to analyze power bus states, drivetrain efficiencies, and runtime under controlled simulated loads."
)

# --- SIDEBAR CONFIGURATION INPUTS ---
st.sidebar.header("Weight Specifications")
frame_weight = st.sidebar.number_input(
    label="Aluminum Frame Weight (lbs)", 
    min_value=10.0, max_value=300.0, value=80.0, step=5.0,
    help="Target bare structural frame weight."
)
components_weight = st.sidebar.number_input(
    label="Motors & Gearboxes Weight (lbs)", 
    min_value=0.0, max_value=300.0, value=45.0, step=5.0,
    help="Weight of the traction motors, ICE generator set, wiring, and enclosures."
)

# --- PHYSICAL BATTERY CONFIGURATION MATRIX ---
st.sidebar.header("Battery Bank Sizing Options")
battery_option = st.sidebar.selectbox(
    label="Select Industrial LiFePO4 Configuration",
    options=[
        "24V 20Ah - Lightweight Pack",
        "24V 40Ah - Extended Range Pack",
        "48V 15Ah - High-Voltage Compact Pack",
        "48V 30Ah - High-Power Industrial Pack",
        "Custom Parameters Pack"
    ]
)

# Deterministic hardware matrix definitions mapping Voltage, Amp-Hours, and Physical Weights
if battery_option == "24V 20Ah - Lightweight Pack":
    pack_voltage = 24.0
    pack_ah = 20.0
    battery_weight_lbs = 11.5
    battery_capacity = pack_voltage * pack_ah
    battery_suggestion = "Optimal for flat indoor testing tracks or light payloads. Keeps vehicle dry mass low."
elif battery_option == "24V 40Ah - Extended Range Pack":
    pack_voltage = 24.0
    pack_ah = 40.0
    battery_weight_lbs = 22.8
    battery_capacity = pack_voltage * pack_ah
    battery_suggestion = "Provides longer operating life cycles on flat terrain, but incurs a minor weight penalty."
elif battery_option == "48V 15Ah - High-Voltage Compact Pack":
    pack_voltage = 48.0
    pack_ah = 15.0
    battery_weight_lbs = 16.5
    battery_capacity = pack_voltage * pack_ah
    battery_suggestion = "Excellent balance. Higher 48V bus minimizes cable heating losses and matches modern motor inverters."
elif battery_option == "48V 30Ah - High-Power Industrial Pack":
    pack_voltage = 48.0
    pack_ah = 30.0
    battery_weight_lbs = 31.2
    battery_capacity = pack_voltage * pack_ah
    battery_suggestion = "Heavy duty sizing. Best choice if executing continuous uphill testing, but pushes frame weight boundaries."
else:
    pack_voltage = st.sidebar.number_input("Custom Bus Nominal Voltage (V)", min_value=12.0, max_value=96.0, value=48.0, step=12.0)
    pack_ah = st.sidebar.number_input("Custom Capacity rating (Ah)", min_value=1.0, max_value=200.0, value=25.0, step=5.0)
    battery_weight_lbs = st.sidebar.number_input("Custom Battery Pack Mass (lbs)", min_value=1.0, max_value=150.0, value=25.0, step=1.0)
    battery_capacity = pack_voltage * pack_ah
    battery_suggestion = "User custom design parameters loop. Verify cell block safety ratings before deployment."

st.sidebar.header("Electrical Generation")
generator_watts = st.sidebar.number_input(
    label="ICE Generator Output (Watts)", 
    min_value=0.0, max_value=5000.0, value=800.0, step=5.0,
    help="Continuous power generation capability of the hybrid unit."
)

st.sidebar.header("Environment & Mission")
soil_coeff = st.sidebar.number_input(label="Soil Rolling Resistance (C_rr)", min_value=0.01, max_value=0.30, value=0.06, step=0.01)
slope_deg = st.sidebar.number_input(label="Field Slope Incline (Degrees)", min_value=0.0, max_value=30.0, value=1.0, step=0.5)
speed = st.sidebar.number_input(label="Target Travel Speed (m/s)", min_value=0.1, max_value=5.0, value=1.2, step=0.1)

st.sidebar.header("Motor Architecture")
motor_type = st.sidebar.selectbox(
    label="Electric Motor Technology Type",
    options=["Permanent Magnet (BLDC/PMSM)", "AC Induction Motor", "Brushed DC Motor"]
)

# --- SYSTEM INTEGRATION LOGIC SWITCHES ---
if motor_type == "Permanent Magnet (BLDC/PMSM)":
    motor_efficiency = 0.88
    motor_notes = "High torque density. Recommended for maintaining strict weight-to-power targets."
elif motor_type == "AC Induction Motor":
    motor_efficiency = 0.80
    motor_notes = "Rugged design, but adding slip losses reduces net operating efficiency."
else:
    motor_efficiency = 0.70
    motor_notes = "Low upfront cost, but mechanical brush wear reduces system performance."

# --- PROPORTIONAL WEIGHT & MEASUREMENT TRANSFORMATIONS ---
total_rover_dry_weight_lbs = frame_weight + components_weight + battery_weight_lbs
total_rover_dry_mass_kg = total_rover_dry_weight_lbs * 0.45359237
series_cells = int(np.ceil(pack_voltage / 3.2))

# --- HIGH-CEILING DESIGN REGULATOR ---
st.subheader("⚠️ Structural Design Envelope Monitor")
if total_rover_dry_weight_lbs > 175.0:
    st.error(f"CRITICAL DESIGN ERROR: Total vehicle weight ({total_rover_dry_weight_lbs:.1f} lbs) exceeds the maximum project specification constraint of 175.0 lbs!")
elif total_rover_dry_weight_lbs > 150.0:
    st.warning(f"DESIGN WARNING: Total vehicle weight ({total_rover_dry_weight_lbs:.1f} lbs) has climbed above your optimal target weight of 150.0 lbs.")
else:
    st.success(f"DESIGN OPTIMAL: Total vehicle dry weight is currently standing at {total_rover_dry_weight_lbs:.1f} lbs (Within the 150.0 lbs engineering target layout).")

# Setup simulated trailing drag loads in pounds
simulated_drag_loads_lbs = np.arange(0, 150, 5) 
electric_runtimes = []
hybrid_runtimes = []

slope_rad = np.radians(slope_deg)

# Baseline metrics (0 lbs added simulated load)
baseline_f_roll = total_rover_dry_mass_kg * 9.81 * soil_coeff * np.cos(slope_rad)
baseline_f_grade = total_rover_dry_mass_kg * 9.81 * np.sin(slope_rad)
baseline_demand = (((baseline_f_roll + baseline_f_grade) * speed) / motor_efficiency) + 45 

# Peak calculations at the extreme 150 lbs simulation stress point
max_total_mass_kg = (total_rover_dry_weight_lbs + 150.0) * 0.45359237
max_f_roll = max_total_mass_kg * 9.81 * soil_coeff * np.cos(slope_rad)
max_f_grade = max_total_mass_kg * 9.81 * np.sin(slope_rad)
peak_mechanical_watts = (max_f_roll + max_f_grade) * speed
peak_horsepower = peak_mechanical_watts / 745.7

usable_battery = battery_capacity * 0.80 

for load_lbs in simulated_drag_loads_lbs:
    total_moving_mass_kg = (total_rover_dry_weight_lbs + load_lbs) * 0.45359237
    f_rolling = total_moving_mass_kg * 9.81 * soil_coeff * np.cos(slope_rad)
    f_grade = total_moving_mass_kg * 9.81 * np.sin(slope_rad)
    tractive_force = f_rolling + f_grade
    
    mechanical_power = tractive_force * speed
    electrical_demand = (mechanical_power / motor_efficiency) + 45
    
    hours_elec = usable_battery / electrical_demand
    electric_runtimes.append(hours_elec)
    
    if generator_watts >= electrical_demand:
        hours_hybrid = 24.0
    else:
        hours_hybrid = usable_battery / (electrical_demand - generator_watts)
    hybrid_runtimes.append(hours_hybrid)

# --- TELEMETRY GRAPHICS ENGINE ---
stress_percentage = min(baseline_demand / 1000.0, 1.0)
motor_red = int(26 + (220 - 26) * stress_percentage)
motor_green = int(32 + (40 - 32) * stress_percentage)
motor_blue = int(44 + (40 - 44) * stress_percentage)
motor_color = f"rgb({motor_red}, {motor_green}, {motor_blue})"

if generator_watts >= baseline_demand:
    bat_glow = "#00FF66"
    status_text = "SYSTEM GENERATOR STATE STABLE"
    hybrid_card_status = "Net Charging [Positive]"
else:
    bat_glow = "#FF3333"
    status_text = "BATTERY NET DEFICIT DRAW ACTIVE"
    hybrid_card_status = "Net Discharging [Deficit]"

st.markdown("### Real-Time System Load Telemetry")

rover_blueprint = f"""
<div style="text-align: center; background-color: #1a202c; padding: 25px; border-radius: 12px; border: 2px solid #2d3748; margin-bottom: 25px;">
    <div style="color: #a0aec0; font-family: sans-serif; font-size: 12px; margin-bottom: 10px; font-weight: bold; letter-spacing: 1px;">
        STATUS: <span style="color: {bat_glow};">{status_text}</span> | POWER BUS DRAW: {baseline_demand:.1f} W
    </div>
    <svg width="550" height="180" viewBox="0 0 550 180" xmlns="http://w3.org">
        <line x1="20" y1="150" x2="530" y2="150" stroke="#4a5568" stroke-width="4" stroke-dasharray="5,5"/>
        <path d="M 50 115 L 120 115" stroke="#718096" stroke-width="6" stroke-linecap="round"/>
        <rect x="15" y="90" width="35" height="50" rx="4" fill="#4a5568" stroke="#2d3748" stroke-width="2"/>
        <text x="18" y="75" font-family="sans-serif" font-size="9" fill="#a0aec0" font-weight="bold">LOAD SLED</text>
        <rect x="120" y="60" width="280" height="65" rx="8" fill="#2d3748" stroke="#4a5568" stroke-width="3"/>
        <rect x="135" y="45" width="100" height="18" rx="4" fill="#cbd5e0" stroke="#718096" stroke-width="2"/>
        <text x="138" y="58" font-family="sans-serif" font-size="8" fill="#1a202c" font-weight="bold">HYBRID GEN: {generator_watts:.0f}W</text>
        <rect x="250" y="45" width="135" height="18" rx="4" fill="#2b6cb0" stroke="{bat_glow}" stroke-width="2.5"/>
        <text x="256" y="58" font-family="sans-serif" font-size="8" fill="white" font-weight="bold">LiFePO4: {battery_capacity:.0f}Wh ({pack_voltage:.0f}V)</text>
        <circle cx="170" cy="125" r="26" fill="{motor_color}" stroke="#718096" stroke-width="3"/>
        <circle cx="170" cy="125" r="8" fill="#cbd5e0"/>
        <circle cx="350" cy="125" r="26" fill="{motor_color}" stroke="#718096" stroke-width="3"/>
        <text x="145" y="170" font-family="sans-serif" font-size="10" fill="#a0aec0" font-weight="bold">M_Front</text>
        <text x="330" y="170" font-family="sans-serif" font-size="10" fill="#a0aec0" font-weight="bold">M_Rear</text>

