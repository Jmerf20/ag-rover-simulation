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

st.sidebar.header("Powertrain Architecture")
transmission_efficiency = st.sidebar.slider(
    label="Gearbox/Transmission Efficiency (η_gear)",
    min_value=0.70, max_value=1.00, value=0.92, step=0.01,
    help="Accounts for mechanical friction losses in gear meshing and bearings before reaching wheels."
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

st.sidebar.header("Electrical Generation & Fuel")
generator_watts = st.sidebar.number_input(
    label="ICE Generator Output (Watts)", 
    min_value=0.0, max_value=2000.0, value=350.0, step=25.0,
    help="Continuous power generation capability of the small hybrid unit."
)
fuel_tank_liters = st.sidebar.number_input(
    label="Fuel Tank Capacity (Liters)",
    min_value=0.5, max_value=10.0, value=2.0, step=0.5,
    help="Volume of gasoline fuel payload capacity onboard."
)
fuel_weight_lbs = fuel_tank_liters * 1.63 # Approx 1.63 lbs per liter of gasoline

st.sidebar.header("Environment & Mission")
soil_coeff = st.sidebar.number_input(label="Soil Rolling Resistance (C_rr)", min_value=0.01, max_value=0.30, value=0.06, step=0.01)
slope_deg = st.sidebar.number_input(label="Field Slope Incline (Degrees)", min_value=0.0, max_value=30.0, value=1.0, step=0.5)
speed = st.sidebar.number_input(label="Target Travel Speed (m/s)", min_value=0.1, max_value=3.0, value=1.0, step=0.1)

st.sidebar.header("Motor Architecture")
motor_type = st.sidebar.selectbox(
    label="Electric Motor Technology Type",
    options=["Permanent Magnet (BLDC/PMSM)", "AC Induction Motor", "Brushed DC Motor"]
)

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
total_rover_dry_weight_lbs = frame_weight + components_weight + battery_weight_lbs + fuel_weight_lbs
total_rover_dry_mass_kg = total_rover_dry_weight_lbs * 0.45359237
series_cells = int(np.ceil(pack_voltage / 3.2))

# --- DESIGN ENVELOPE MONITOR (STRICT 200 LBS CEILING) ---
st.subheader("Structural Design Envelope Monitor")
if total_rover_dry_weight_lbs > 200.0:
    st.error(f"CRITICAL DESIGN ERROR: Total vehicle weight ({total_rover_dry_weight_lbs:.1f} lbs) exceeds maximum allowed project limit of 200.0 lbs!")
elif total_rover_dry_weight_lbs > 180.0:
    st.warning(f"DESIGN WARNING: Total vehicle weight ({total_rover_dry_weight_lbs:.1f} lbs) has climbed dangerously close to your 200.0 lbs maximum ceiling.")
else:
    st.success(f"DESIGN OPTIMAL: Total vehicle dry weight is standing cleanly at {total_rover_dry_weight_lbs:.1f} lbs (Safe within the 200.0 lbs project target timeline).")

# Sweeping internal added payload mass variations purely in pounds
simulated_payload_loads_lbs = np.arange(0, 101, 5) 
electric_runtimes = []
hybrid_runtimes = []

slope_rad = np.radians(slope_deg)

# Baseline evaluation metrics (0 lbs added internal payload)
baseline_f_roll = total_rover_dry_mass_kg * 9.81 * soil_coeff * np.cos(slope_rad)
baseline_f_grade = total_rover_dry_mass_kg * 9.81 * np.sin(slope_rad)
# Added transmission_efficiency penalty below
baseline_demand = (((baseline_f_roll + baseline_f_grade) * speed) / (motor_efficiency * transmission_efficiency)) + 20 

# Peak calculations at max 100 lbs internal carrying limits
max_total_mass_kg = (total_rover_dry_weight_lbs + 100.0) * 0.45359237
max_f_roll = max_total_mass_kg * 9.81 * soil_coeff * np.cos(slope_rad)
max_f_grade = max_total_mass_kg * 9.81 * np.sin(slope_rad)
peak_mechanical_watts = (max_f_roll + max_f_grade) * speed
peak_horsepower = peak_mechanical_watts / 745.7

# --- FUEL EFFICIENCY CALCULATIONS ---
bsfc_g_kwh = 380.0 # Standard brake specific fuel consumption constant
fuel_burn_g_per_min = (generator_watts / 1000.0) * bsfc_g_kwh / 60.0
fuel_burn_liters_per_min = fuel_burn_g_per_min / 740.0 # Gasoline density conversion index

if fuel_burn_liters_per_min > 0:
    exact_fuel_runtime_mins = fuel_tank_liters / fuel_burn_liters_per_min
else:
    exact_fuel_runtime_mins = 0.0

for payload_lbs in simulated_payload_loads_lbs:
    total_moving_mass_kg = (total_rover_dry_weight_lbs + payload_lbs) * 0.45359237
    f_rolling = total_moving_mass_kg * 9.81 * soil_coeff * np.cos(slope_rad)
    f_grade = total_moving_mass_kg * 9.81 * np.sin(slope_rad)
    tractive_force = f_rolling + f_grade
    
    mechanical_power = tractive_force * speed
    # Added transmission_efficiency penalty below
    electrical_demand = (mechanical_power / (motor_efficiency * transmission_efficiency)) + 20
    
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
    bat_glow = "#00FF66"
    status_text = "SYSTEM GENERATOR STATE STABLE"
else:
    hybrid_card_status = "Net Discharging [Deficit Draw]"
    bat_glow = "#FF3333"
    status_text = "BATTERY NET DEFICIT DRAW ACTIVE"

# --- DYNAMIC COLOR MECHANICAL OVERHEAD LOGIC ---
stress_percentage = min(baseline_demand / 1000.0, 1.0)
motor_red = int(26 + (220 - 26) * stress_percentage)
motor_green = int(32 + (40 - 32) * stress_percentage)
motor_blue = int(44 + (40 - 44) * stress_percentage)
motor_color = f"rgb({motor_red}, {motor_green}, {motor_blue})"

# --- NATIVE GRAPHICAL ROVER DIAGRAM ---
st.markdown("### Real-Time System Load Telemetry")

# Using single quotes for the f-string to prevent breaking the IDE python syntax highlighting block
rover_blueprint = f'''
<div style="text-align: center; background-color: #1a202c; padding: 25px; border-radius: 12px; border: 2px solid #2d3748; margin-bottom: 25px;">
    <div style="color: #a0aec0; font-family: sans-serif; font-size: 12px; margin-bottom: 10px; font-weight: bold; letter-spacing: 1px;">
        STATUS: <span style="color: {bat_glow};">{status_text}</span> | POWER BUS DRAW: {baseline_demand:.1f} W
    </div>
    <svg width="550" height="180" viewBox="0 0 550 180" xmlns="http://w3.org">
        <line x1="20" y1="150" x2="530" y2="150" stroke="#4a5568" stroke-width="4" stroke-dasharray="5,5"/>
        <path d="M 50 115 L 120 115" stroke="#718096" stroke-width="6" stroke-linecap="round"/>
        <rect x="15" y="100" width="40" height="40" rx="3" fill="#4a5568" stroke="#2d3748" stroke-width="2"/>
        <text x="18" y="88" font-family="sans-serif" font-size="8" fill="#a0aec0" font-weight="bold">LOAD SLED</text>
        <rect x="120" y="60" width="280" height="65" rx="8" fill="#2d3748" stroke="#4a5568" stroke-width="3"/>
        <rect x="135" y="45" width="100" height="18" rx="4" fill="#cbd5e0" stroke="#718096" stroke-width="2"/>
        <text x="138" y="57" font-family="sans-serif" font-size="8" fill="#1a202c" font-weight="bold">HYBRID GEN: {generator_watts:.0f}W</text>
        <rect x="250" y="45" width="135" height="18" rx="4" fill="#2b6cb0" stroke="{bat_glow}" stroke-width="2.5"/>
        <text x="256" y="57" font-family="sans-serif" font-size="8" fill="white" font-weight="bold">LiFePO4: {battery_capacity:.0f}Wh ({pack_voltage:.0f}V)</text>
        <circle cx="170" cy="125" r="26" fill="{motor_color}" stroke="#718096" stroke-width="3"/>
        <circle cx="170" cy="125" r="8" fill="#cbd5e0"/>
        <circle cx="350" cy="125" r="26" fill="{motor_color}" stroke="#718096" stroke-width="3"/>
        <circle cx="350" cy="125" r="8" fill="#cbd5e0"/>
        <text x="145" y="170" font-family="sans-serif" font-size="10" fill="#a0aec0" font-weight="bold">M_Front</text>
        <text x="330" y="170" font-family="sans-serif" font-size="10" fill="#a0aec0" font-weight="bold">M_Rear</text>
        <text x="432" y="73" font-family="sans-serif" font-size="10" fill="#cbd5e0" font-weight="bold">v = {speed:.1f} m/s</text>
    </svg>
</div>
'''

st.components.v1.html(rover_blueprint, height=250)

# --- EXPANDED RUNTIME CALLOUT PANEL ---
st.subheader("⏱️ Precise System Sizing Predictions")
calc_col1, calc_col2 = st.columns(2)

with calc_col1:
    if exact_fuel_runtime_mins > 0:
        st.info(f"⛽ **Generator Operating Scope:** Your chosen {fuel_tank_liters:.1f}L tank yields exactly **{exact_fuel_runtime_mins:.1f} operating minutes** of continuous generator power at {generator_watts:.0f}W output.")
    else:
        st.info("⛽ **Generator Inactive:** Fuel output set to 0W.")

with calc_col2:
    if generator_watts >= baseline_demand:
        st.success("🔋 **Battery Reserves Stable:** Generation completely covers or exceeds baseline traction loads. Battery reserves preserved.")
    else:
        net_drain = baseline_demand - generator_watts
        exact_battery_mins = (usable_battery / net_drain) * 60.0
        st.error(f"⚠️ **Battery Depletion Warning:** Continuous deficit active. Battery reserves will deplete in **{exact_battery_mins:.1f} minutes** under baseline load.")

# --- HARDWARE SIZING RECAP ---
st.subheader("Automated Hardware Sizing Recommendations")
rec_col1, rec_col2 = st.columns(2)

with rec_col1:
    st.info(
        f"**Battery Architecture Selection Summary:**\n\n"
        f"* Selected Bank Energy: {battery_capacity:.0f} Wh\n"
        f"* Nominal Operating Bus: {pack_voltage:.0f} V | Capacity: {pack_ah:.0f} Ah\n"
        f"* Safe Usable Energy Target (80% DoD): {usable_battery:.0f} Wh\n"
        f"* Internal Arrangement: {series_cells}S Cell Stack\n\n"
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
    st.metric(label="Total Vehicle Gross Weight", value=f"{total_rover_dry_weight_lbs:.1f} lbs")
with col2:
    st.metric(label="Baseline System Demand", value=f"{baseline_demand:.1f} W")
    st.metric(label="Usable Energy Storage Buffer", value=f"{usable_battery:.0f} Wh")
with col3:
    st.metric(label="Baseline Power Bus State", value=hybrid_card_status)

# --- VISUALIZATION ENGINE GENERATION ---
fig = go.Figure()

# Add a vibrant, thick line for pure battery mode
fig.add_trace(go.Scatter(
    x=simulated_payload_loads_lbs, 
    y=electric_runtimes, 
    name="Pure Electric Mode (Gen Off)", 
    mode="lines+markers",
    line=dict(color='#FF4B4B', width=4),
    marker=dict(size=6)
))

# Add a striking line for hybrid mode showing real slope changes
fig.add_trace(go.Scatter(
    x=simulated_payload_loads_lbs, 
    y=hybrid_runtimes, 
    name="Series Hybrid Mode (Gen Active)", 
    mode="lines+markers",
    line=dict(color='#0068C9', width=4),
    marker=dict(size=6)
))

# Polish layout styling to look like a high-end engineering dashboard
fig.update_layout(
    title=dict(
        text="Powertrain Sensitivity Analysis: Payload vs. Continuous Operational Sizing",
        font=dict(size=16, color='#F8FAFC', family='sans-serif')
    ),
    xaxis=dict(
        title="Added Cargo Payload Weight (lbs)",
        titlefont=dict(color='#94A3B8'),
        tickfont=dict(color='#cbd5e1'),
        gridcolor='#334155',
        zerolinecolor='#475569'
    ),
    yaxis=dict(
        title="Continuous Mission Runtime (Hours)",
        titlefont=dict(color='#94A3B8'),
        tickfont=dict(color='#cbd5e1'),
        gridcolor='#334155',
        zerolinecolor='#475569',
        range=[0, 25]
    ),
    background_color='rgba(0,0,0,0)',
    paper_bgcolor='#1a202c',
    plot_bgcolor='#1a202c',
    margin=dict(l=50, r=30, t=60, b=50),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(color='#cbd5e1')
    )
)

st.plotly_chart(fig, use_container_width=True)



