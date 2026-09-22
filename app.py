import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.set_page_config(layout="wide")

# --- FORMAL ACADEMIC TITLE ---
st.title("Series Ag-Rover Run Time Simulation")
st.write(
    "A custom predictive sizing model developed by electrical and mechanical engineering students "
    "to analyze power bus states, drivetrain efficiencies, and runtime under compact vehicle constraints."
)

# --- SIDEBAR CONFIGURATION INPUTS ---
st.sidebar.header("Weight Specifications")
frame_weight = st.sidebar.number_input(
    label="Aluminum Frame Weight (lbs)", 
    min_value=5.0, max_value=150.0, value=40.0, step=5.0,
    help="Target bare structural frame weight."
)
components_weight = st.sidebar.number_input(
    label="Motors & Gearboxes Weight (lbs)", 
    min_value=0.0, max_value=150.0, value=25.0, step=5.0,
    help="Weight of the traction motors, electronics, and enclosures."
)

# --- LIGHTWEIGHT ROBOTICS BATTERY SELECTION MATRIX ---
st.sidebar.header("Compact Battery Options")
battery_option = st.sidebar.selectbox(
    label="Select Robotics LiFePO4 Configuration",
    options=[
        "12V 10Ah - Ultra-Compact Pack (3.2 lbs)",
        "12V 20Ah - Standard Robotic Pack (5.5 lbs)",
        "24V 10Ah - High-Voltage Slim Pack (6.4 lbs)",
        "24V 20Ah - Max Endurance Pack (11.2 lbs)"
    ]
)

# Extracting physical parameters from hardware option selection
if battery_option == "12V 10Ah - Ultra-Compact Pack (3.2 lbs)":
    pack_voltage = 12.0
    pack_ah = 10.0
    battery_weight_lbs = 3.2
    battery_suggestion = "Lightest profile. Optimizes vehicle agility for low-speed navigation tracks."
elif battery_option == "12V 20Ah - Standard Robotic Pack (5.5 lbs)":
    pack_voltage = 12.0
    pack_ah = 20.0
    battery_weight_lbs = 5.5
    battery_suggestion = "Standard baseline robotics footprint. Balanced weight-to-energy density ratio."
elif battery_option == "24V 10Ah - High-Voltage Slim Pack (6.4 lbs)":
    pack_voltage = 24.0
    pack_ah = 10.0
    battery_weight_lbs = 6.4
    battery_suggestion = "Higher voltage bus limits system copper losses and reduces internal thermal generation."
else:
    pack_voltage = 24.0
    pack_ah = 20.0
    battery_weight_lbs = 11.2
    battery_suggestion = "Maximum stored energy capability within the structural design weight budget."

battery_capacity = pack_voltage * pack_ah
usable_battery = battery_capacity * 0.80  # Hardcoded 80% safe Depth of Discharge limit

st.sidebar.header("Electrical Generation")
generator_watts = st.sidebar.number_input(
    label="ICE Generator Output (Watts)", 
    min_value=0.0, max_value=2000.0, value=350.0, step=25.0,
    help="Continuous power generation capability of the small hybrid unit."
)

st.sidebar.header("Environment & Mission")
soil_coeff = st.sidebar.number_input(label="Soil Rolling Resistance (C_rr)", min_value=0.01, max_value=0.30, value=0.06, step=0.01)
slope_deg = st.sidebar.number_input(label="Field Slope Incline (Degrees)", min_value=0.0, max_value=30.0, value=1.0, step=0.5)
speed = st.sidebar.number_input(label="Target Travel Speed (m/s)", min_value=0.1, max_value=3.0, value=1.0, step=0.1)

st.sidebar.header("Motor Architecture")
motor_type = st.sidebar.selectbox(
    label="Electric Motor Technology Type",
    options=["Permanent Magnet (BLDC/PMSM)", "AC Induction Motor", "Brushed DC Motor"]
)

# Motor constant allocation filters
if motor_type == "Permanent Magnet (BLDC/PMSM)":
    motor_efficiency = 0.88
    motor_notes = "High efficiency. Best choice for small, power-limited robotic rovers."
elif motor_type == "AC Induction Motor":
    motor_efficiency = 0.80
    motor_notes = "Rugged design profile, though internal slip fields lower overall runtime."
else:
    motor_efficiency = 0.70
    motor_notes = "Low component cost, but carbon brush friction compromises system performance."

# --- SYSTEM MASS & PHYSICS MATRIC CONVERSIONS ---
total_rover_dry_weight_lbs = frame_weight + components_weight + battery_weight_lbs
total_rover_dry_mass_kg = total_rover_dry_weight_lbs * 0.45359237
series_cells = int(np.ceil(pack_voltage / 3.2))

# --- DESIGN ENVELOPE MONITOR ---
st.subheader("Structural Design Envelope Monitor")
if total_rover_dry_weight_lbs > 175.0:
    st.error(f"CRITICAL DESIGN ERROR: Total vehicle weight ({total_rover_dry_weight_lbs:.1f} lbs) exceeds maximum assignment specification limit of 175.0 lbs!")
elif total_rover_dry_weight_lbs > 150.0:
    st.warning(f"DESIGN WARNING: Total vehicle weight ({total_rover_dry_weight_lbs:.1f} lbs) has climbed above your optimal target weight of 150.0 lbs.")
else:
    st.success(f"DESIGN OPTIMAL: Total vehicle dry weight is standing cleanly at {total_rover_dry_weight_lbs:.1f} lbs (Within the 150.0 lbs project target timeline).")

# Sweeping internal added payload mass variations purely in pounds
simulated_payload_loads_lbs = np.arange(0, 101, 5) 
electric_runtimes = []
hybrid_runtimes = []

slope_rad = np.radians(slope_deg)

# Baseline evaluation metrics (0 lbs added internal payload)
baseline_f_roll = total_rover_dry_mass_kg * 9.81 * soil_coeff * np.cos(slope_rad)
baseline_f_grade = total_rover_dry_mass_kg * 9.81 * np.sin(slope_rad)
baseline_demand = (((baseline_f_roll + baseline_f_grade) * speed) / motor_efficiency) + 20  # 20W overhead computing draw

# Peak calculations at max 100 lbs internal carrying limits
max_total_mass_kg = (total_rover_dry_weight_lbs + 100.0) * 0.45359237
max_f_roll = max_total_mass_kg * 9.81 * soil_coeff * np.cos(slope_rad)
max_f_grade = max_total_mass_kg * 9.81 * np.sin(slope_rad)
peak_mechanical_watts = (max_f_roll + max_f_grade) * speed
peak_horsepower = peak_mechanical_watts / 745.7

for payload_lbs in simulated_payload_loads_lbs:
    total_moving_mass_kg = (total_rover_dry_weight_lbs + payload_lbs) * 0.45359237
    f_rolling = total_moving_mass_kg * 9.81 * soil_coeff * np.cos(slope_rad)
    f_grade = total_moving_mass_kg * 9.81 * np.sin(slope_rad)
    tractive_force = f_rolling + f_grade
    
    mechanical_power = tractive_force * speed
    electrical_demand = (mechanical_power / motor_efficiency) + 20
    
    # Pure Battery Sizing Runtime
    hours_elec = usable_battery / electrical_demand
    electric_runtimes.append(hours_elec)
    
    # Series Hybrid Node Sizing Runtime
    if generator_watts >= electrical_demand:
        hours_hybrid = 24.0
    else:
        hours_hybrid = usable_battery / (electrical_demand - generator_watts)
    hybrid_runtimes.append(hours_hybrid)

# Power Distribution Bus Evaluation
if generator_watts >= baseline_demand:
    hybrid_card_status = "Net Charging [Positive Bus Buffer]"
else:
    hybrid_card_status = "Net Discharging [Deficit Draw]"

# --- HARDWARE SIZING RECAP ---
st.subheader("Automated Hardware Sizing Recommendations")
rec_col1, rec_col2 = st.columns(2)

with rec_col1:
    st.info(
        f"**Battery Architecture Selection Summary:**\n\n"
        f"* Selected Bank Energy: **{battery_capacity:.0f} Wh**\n"
        f"* Nominal Operating Bus: **{pack_voltage:.0f} V** | Capacity: **{pack_ah:.0f} Ah**\n"
        f"* Safe Usable Energy Target (80% DoD): **{usable_battery:.0f} Wh**\n"
        f"* Internal Arrangement: **{series_cells}S** Cell Stack\n\n"
        f"**Design Guidance:** {battery_suggestion}"
    )

with rec_col2:
    st.warning(
        f"**Calculated Peak Traction Requirement (At 100 lbs cargo load limit):**\n\n"
        f"* Minimum Continuous Power Required: **{peak_mechanical_watts:.1f} Watts**\n"
        f"* Minimum Continuous Horsepower Required: **{peak_horsepower:.3f} HP**\n\n"
        f"*Engineering Note:* If building a 4WD chassis, each motor must be individually rated for at least **{(peak_mechanical_watts/4.0):.0f} Watts** to prevent electrical winding stall conditions."
    )

# --- METRIC BREAKDOWN PANEL ---
st.subheader("Instant System Breakdown")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Selected Battery Pack Weight", value=f"{battery_weight_lbs:.1f} lbs")
    st.metric(label="Total Vehicle Dry Weight", value=f"{total_rover_dry_weight_lbs:.1f} lbs")
with col2:
    st.metric(label="Baseline System Demand", value=f"{baseline_demand:.1f} W")
    st.metric(label="Usable Energy Storage Buffer", value=f"{usable_battery:.0f} Wh")
with col3:
    st.metric(label="Baseline Power Bus State", value=hybrid_card_status)

# --- VISUALIZATION ENGINE GENERATION ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=simulated_payload_loads_lbs, y=electric_runtimes, name="Pure Electric Mode (Generator Off)", line=dict(color='#FF4B4B', width=3)))
fig.add_trace(go.Scatter(x=simulated_payload_loads_lbs, y=hybrid_runtimes, name="Series Hybrid Mode (Generator Active)", line=dict(color='#0068C9', width=3)))

fig.update_layout(
    title="System Runtime Sensitivity to Internal Added Payload Cargo",
    xaxis_title="Added Payload Weight (lbs)",
    yaxis_title="Continuous Runtime (Hours)",
    yaxis=dict(range=[0, 24]),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig, use_container_width=True)
