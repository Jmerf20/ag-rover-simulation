cat << 'EOF' > app.py
import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.set_page_config(layout="wide")

st.title("Series Ag-Rover Run Time Simulation")
st.write(
    "A predictive sizing and simulation model developed by electrical and mechanical engineering "
    "students to analyze system runtime, component efficiencies, and power distribution bus states "
    "under dynamic field loads."
)

# --- SIDEBAR CONFIGURATION INPUTS ---
st.sidebar.header("System Specifications")
base_weight = st.sidebar.number_input(label="Chassis Dry Mass (kg)", min_value=10.0, max_value=2000.0, value=250.0, step=10.0)
internal_cargo = st.sidebar.number_input(label="Internal Payload Cargo (kg)", min_value=0.0, max_value=2000.0, value=100.0, step=5.0)

st.sidebar.header("Electrical Systems")
battery_capacity = st.sidebar.number_input(label="LiFePO4 Pack Capacity (Wh)", min_value=500.0, max_value=50000.0, value=5000.0, step=500.0)
generator_watts = st.sidebar.number_input(label="ICE Generator Output (Watts)", min_value=0.0, max_value=20000.0, value=2000.0, step=100.0)

st.sidebar.header("Environment & Mission")
soil_coeff = st.sidebar.number_input(label="Soil Rolling Resistance (C_rr)", min_value=0.01, max_value=0.30, value=0.08, step=0.01)
slope_deg = st.sidebar.number_input(label="Field Slope Incline (Degrees)", min_value=0.0, max_value=30.0, value=2.0, step=0.5)
speed = st.sidebar.number_input(label="Target Travel Speed (m/s)", min_value=0.1, max_value=10.0, value=1.5, step=0.1)

# New Motor Configuration Selectors
st.sidebar.header("Motor Architecture")
motor_type = st.sidebar.selectbox(
    label="Electric Motor Technology Type",
    options=["Permanent Magnet (BLDC/PMSM)", "AC Induction Motor", "Brushed DC Motor"],
    help="Brushless options yield highest efficiency. AC Induction provides high durability at lower costs."
)

# Automatically shift the simulation efficiency variable based on the EE motor selection profile
if motor_type == "Permanent Magnet (BLDC/PMSM)":
    motor_efficiency = 0.88
    motor_notes = "High torque density and efficiency. Best choice for autonomous rovers, though hardware cost is higher."
elif motor_type == "AC Induction Motor":
    motor_efficiency = 0.80
    motor_notes = "Extremely rugged and maintenance-free in dusty field mud. Suffers from minor induction slip losses."
else:
    motor_efficiency = 0.70
    motor_notes = "Low component cost, but friction brushes degrade and require manual replacement. Poor energy efficiency."

# --- ADVANCED ENGINEERING PHYSICS ENGINE ---
est_battery_weight = battery_capacity / 100.0
total_structural_mass = base_weight + internal_cargo + est_battery_weight

towing_loads = np.arange(0, 1501, 50)
electric_runtimes = []
hybrid_runtimes = []

usable_battery = battery_capacity * 0.80  
slope_rad = np.radians(slope_deg)          

# Baseline calculations for the current user configuration (at 0 added towed load)
baseline_f_roll = total_structural_mass * 9.81 * soil_coeff * np.cos(slope_rad)
baseline_f_grade = total_structural_mass * 9.81 * np.sin(slope_rad)
baseline_demand = (((baseline_f_roll + baseline_f_grade) * speed) / motor_efficiency) + 150

# Track peak requirements at the absolute maximum 1500 kg implement pulling limit
max_moving_mass = total_structural_mass + 1500.0
max_f_roll = max_moving_mass * 9.81 * soil_coeff * np.cos(slope_rad)
max_f_grade = max_moving_mass * 9.81 * np.sin(slope_rad)
peak_mechanical_watts = (max_f_roll + max_f_grade) * speed
peak_horsepower = peak_mechanical_watts / 745.7

for load in towing_loads:
    total_moving_mass = total_structural_mass + load
    f_rolling = total_moving_mass * 9.81 * soil_coeff * np.cos(slope_rad)
    f_grade = total_moving_mass * 9.81 * np.sin(slope_rad)
    tractive_force = f_rolling + f_grade
    
    mechanical_power = tractive_force * speed
    electrical_demand = (mechanical_power / motor_efficiency) + 150  
    
    hours_elec = usable_battery / electrical_demand
    electric_runtimes.append(hours_elec)
    
    if generator_watts >= electrical_demand:
        hours_hybrid = 24.0  
    else:
        hours_hybrid = usable_battery / (electrical_demand - generator_watts)
    hybrid_runtimes.append(hours_hybrid)

# --- DYNAMIC COLOR LOGIC BASED ON MATH OVERHEAD ---
stress_percentage = min(baseline_demand / 4000.0, 1.0)
motor_red = int(26 + (220 - 26) * stress_percentage)
motor_green = int(32 + (40 - 32) * stress_percentage)
motor_blue = int(44 + (40 - 44) * stress_percentage)
motor_color = f"rgb({motor_red}, {motor_green}, {motor_blue})"

if generator_watts >= baseline_demand:
    bat_glow = "#00FF66" 
    status_text = "CHARGING SYSTEM STABLE"
    hybrid_card_status = "Net Charging [Positive]"
else:
    bat_glow = "#FF3333" 
    status_text = "BATTERY NET DRAIN ACTIVE"
    hybrid_card_status = "Net Discharging [Deficit]"

# --- NATIVE GRAPHICAL ROVER DIAGRAM ---
st.markdown("### Real-Time System Load Telemetry")

rover_blueprint = f"""
<div style="text-align: center; background-color: #1a202c; padding: 25px; border-radius: 12px; border: 2px solid #2d3748; margin-bottom: 25px;">
    <div style="color: #a0aec0; font-family: sans-serif; font-size: 12px; margin-bottom: 10px; font-weight: bold; letter-spacing: 1px;">
        STATUS: <span style="color: {bat_glow};">{status_text}</span> | BUS DRAW: {baseline_demand:.1f} W
    </div>
    <svg width="550" height="180" viewBox="0 0 550 180" xmlns="http://w3.org">
        <!-- Ground Profile -->
        <line x1="20" y1="150" x2="530" y2="150" stroke="#4a5568" stroke-width="4" stroke-dasharray="5,5"/>
        
        <!-- Implement Connection -->
        <path d="M 50 115 L 120 115" stroke="#718096" stroke-width="6" stroke-linecap="round"/>
        <rect x="15" y="90" width="35" height="50" rx="4" fill="#4a5568" stroke="#2d3748" stroke-width="2"/>
        <text x="22" y="75" font-family="sans-serif" font-size="10" fill="#a0aec0" font-weight="bold">PLOW</text>
        
        <!-- Main Chassis -->
        <rect x="120" y="60" width="280" height="65" rx="8" fill="#2d3748" stroke="#4a5568" stroke-width="3"/>
        
        <!-- ICE Gen Box -->
        <rect x="135" y="45" width="100" height="18" rx="4" fill="#cbd5e0" stroke="#718096" stroke-width="2"/>
        <text x="142" y="58" font-family="sans-serif" font-size="9" fill="#1a202c" font-weight="bold">GEN Set: {generator_watts:.0f}W</text>
        
        <!-- Reactive LiFePO4 Box -->
        <rect x="250" y="45" width="135" height="18" rx="4" fill="#2b6cb0" stroke="{bat_glow}" stroke-width="2.5"/>
        <text x="262" y="58" font-family="sans-serif" font-size="9" fill="white" font-weight="bold">LiFePO4: {battery_capacity:.0f}Wh</text>
        
        <!-- Reactive Wheel Assemblies -->
        <circle cx="170" cy="125" r="26" fill="{motor_color}" stroke="#718096" stroke-width="3"/>
        <circle cx="170" cy="125" r="8" fill="#cbd5e0"/>
        
        <circle cx="350" cy="125" r="26" fill="{motor_color}" stroke="#718096" stroke-width="3"/>
        <circle cx="350" cy="125" r="8" fill="#cbd5e0"/>
        
        <!-- Drive Hub Telemetry Annotations -->
        <text x="145" y="170" font-family="sans-serif" font-size="10" fill="#a0aec0" font-weight="bold">M_Front</text>
        <text x="330" y="170" font-family="sans-serif" font-size="10" fill="#a0aec0" font-weight="bold">M_Rear</text>
        
        <!-- Dynamic Forward Velocity Vector Arrow -->
        <path d="M 430 90 L 480 90 M 465 80 L 480 90 L 465 100" stroke="{bat_glow}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        <text x="432" y="73" font-family="sans-serif" font-size="10" fill="#cbd5e0" font-weight="bold">v = {speed:.1f} m/s</text>
    </svg>
</div>
"""
st.components.v1.html(rover_blueprint, height=250)

# --- NEW AUTOMATED MOTOR RECOMMENDATION PANEL ---
st.subheader("📋 Automated Hardware Design Recommendations")
rec_col1, rec_col2 = st.columns(2)

with rec_col1:
    st.info(f"**Selected Architecture Profile:** {motor_type}\n\n*Engineering Context:* {motor_notes}")

with rec_col2:
    st.warning(
        f"**Calculated Peak Traction Requirement (At 1500 kg load limit):**\n\n"
        f"* Minimum Total Power: **{peak_mechanical_watts:.1f} Watts**\n"
        f"* Minimum Total Horsepower: **{peak_horsepower:.2f} HP**\n\n"
        f"*Sizing Guide:* If building a 4WD rover, next semester's team must source 4 distinct motors rated for at least **{(peak_mechanical_watts/4.0):.0f} Watts** each."
    )

# --- LIVE DATA DISPLAY CARDS ---
st.subheader("Instant System Breakdown")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Estimated Battery Pack Mass", value=f"{est_battery_weight:.1f} kg")
    st.metric(label="Total Unloaded Vehicle Mass", value=f"{total_structural_mass:.1f} kg")
with col2:
    st.metric(label="Baseline Bus Power Demand", value=f"{baseline_demand:.1f} W")
    st.metric(label="Usable Operational Energy Capacity", value=f"{usable_battery:.0f} Wh")
with col3:
    st.metric(label="Baseline Power Bus State", value=hybrid_card_status)

# --- CHART GENERATION ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=towing_loads, y=electric_runtimes, name="Pure Electric Mode (Engine Off)", line=dict(color='#FF4B4B', width=3)))
fig.add_trace(go.Scatter(x=towing_loads, y=hybrid_runtimes, name="Series Hybrid Mode (Generator Active)", line=dict(color='#0068C9', width=3)))

fig.update_layout(
    title="System Runtime Sensitivity to Implement Pull Load",
    xaxis_title="Towed Drawbar Load (kg)",
    yaxis_title="Continuous Runtime (Hours)",
    yaxis=dict(range=[0, 25]),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig, use_container_width=True)
EOF
