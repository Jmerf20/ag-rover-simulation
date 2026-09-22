import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd

st.set_page_config(layout="wide")

# --- FORMAL ACADEMIC TITLE ---
st.title("Advanced Series Ag-Rover Transient Sizing & Mission Simulation")
st.write(
    "A high-fidelity time-stepping predictive model analyzing transient power bus dynamics, "
    "internal resistance (I²R) losses, transmission friction anomalies, and ICE fuel burn profiles over operational timelines."
)

# --- SIDEBAR CONFIGURATION INPUTS ---
st.sidebar.header("⚖️ Mechanical Weight Sizing")
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

st.sidebar.header("⚙️ Drivetrain Architecture")
transmission_efficiency = st.sidebar.slider(
    label="Gearbox/Transmission Efficiency (η_gear)",
    min_value=0.70, max_value=1.00, value=0.92, step=0.01,
    help="Accounts for mechanical friction losses in gear meshing and bearings before reaching wheels."
)

# --- EE ADVANCED INPUTS ---
st.sidebar.header("⚡ Electrical Systems (EE Focus)")
wire_gauge = st.sidebar.selectbox(
    label="Wiring Harness Cable Gauge (AWG)",
    options=["10 AWG (Thick - 1.0 mΩ/ft)", "12 AWG (Standard - 1.6 mΩ/ft)", "14 AWG (Thin - 2.5 mΩ/ft)"]
)
wire_length = st.sidebar.slider(
    label="Total Cable Loop Run Length (Feet)",
    min_value=2.0, max_value=30.0, value=12.0, step=1.0,
    help="Total length of wiring harness copper path carrying heavy motor current."
)

# Allocate wire resistance values per foot based on physics standards
if "10 AWG" in wire_gauge:
    r_wire_per_foot = 0.000998
elif "12 AWG" in wire_gauge:
    r_wire_per_foot = 0.001588
else:
    r_wire_per_foot = 0.002525
total_wire_resistance = r_wire_per_foot * wire_length

# --- LIGHTWEIGHT ROBOTICS BATTERY SELECTION MATRIX ---
st.sidebar.header("🔋 Compact Battery & Internal Resistance")
battery_option = st.sidebar.selectbox(
    label="Select Robotics LiFePO4 Configuration",
    options=[
        "12V 10Ah - Ultra-Compact Pack (R_int: 30 mΩ)",
        "12V 20Ah - Standard Robotic Pack (R_int: 18 mΩ)",
        "24V 10Ah - High-Voltage Slim Pack (R_int: 24 mΩ)",
        "24V 20Ah - Max Endurance Pack (R_int: 12 mΩ)"
    ]
)

# Extracting electrical physical parameters + internal resistance properties
if "12V 10Ah" in battery_option:
    pack_voltage = 12.0
    pack_ah = 10.0
    battery_weight_lbs = 3.2
    r_internal = 0.030 
elif "12V 20Ah" in battery_option:
    pack_voltage = 12.0
    pack_ah = 20.0
    battery_weight_lbs = 5.5
    r_internal = 0.018
elif "24V 10Ah" in battery_option:
    pack_voltage = 24.0
    pack_ah = 10.0
    battery_weight_lbs = 6.4
    r_internal = 0.024
else:
    pack_voltage = 24.0
    pack_ah = 20.0
    battery_weight_lbs = 11.2
    r_internal = 0.012

battery_capacity_wh = pack_voltage * pack_ah
usable_battery_wh = battery_capacity_wh * 0.80  # 80% safe Depth of Discharge (DoD) constraint

st.sidebar.header("⛽ Hybrid Energy Node")
generator_watts = st.sidebar.number_input(
    label="ICE Generator Output (Watts)", 
    min_value=0.0, max_value=2000.0, value=350.0, step=25.0,
    help="Continuous power output capability of the hybrid IC engine module."
)
fuel_tank_liters = st.sidebar.number_input(
    label="Fuel Tank Capacity (Liters)",
    min_value=0.5, max_value=10.0, value=2.0, step=0.5,
    help="Volume of gasoline payload capacity onboard."
)
fuel_weight_lbs = fuel_tank_liters * 1.63  # Fuel mass conversion scaling dynamically (approx 1.63 lbs per liter)

st.sidebar.header("🏁 Mission Parameters")
simulation_minutes = st.sidebar.slider("Total Mission Sim Duration (Minutes)", 10, 180, 60, 5)

# --- MOTOR ARCHITECTURE ---
st.sidebar.header("⚙️ Motor Parameters")
motor_type = st.sidebar.selectbox(
    label="Electric Motor Technology Type",
    options=["Permanent Magnet (BLDC/PMSM)", "AC Induction Motor", "Brushed DC Motor"]
)

if motor_type == "Permanent Magnet (BLDC/PMSM)":
    motor_efficiency = 0.88
elif motor_type == "AC Induction Motor":
    motor_efficiency = 0.80
else:
    motor_efficiency = 0.70

# --- DYNAMIC MULTI-PHASE FIELD MISSION TIMELINE CREATOR ---
st.subheader("🛠️ Step 1: Design the Field Mission Profile Timeline")
st.write("Divide your timeline into three chronological segments to observe how varying soil and slope spikes deplete the electrical bus.")

m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    st.markdown("**Phase A (First 33% of time)**")
    cr_A = st.slider("Soil Resistance A (C_rr)", 0.02, 0.25, 0.05, 0.01, key="cra")
    slope_A = st.slider("Slope A (Degrees)", 0.0, 20.0, 1.0, 0.5, key="sla")
    speed_A = st.slider("Speed A (m/s)", 0.2, 3.0, 1.2, 0.1, key="spa")
with m_col2:
    st.markdown("**Phase B (Middle 33% of time)**")
    cr_B = st.slider("Soil Resistance B (C_rr)", 0.02, 0.25, 0.14, 0.01, key="crb")
    slope_B = st.slider("Slope B (Degrees)", 0.0, 20.0, 6.0, 0.5, key="slb")
    speed_B = st.slider("Speed B (m/s)", 0.2, 3.0, 0.8, 0.1, key="spb")
with m_col3:
    st.markdown("**Phase C (Final 34% of time)**")
    cr_C = st.slider("Soil Resistance C (C_rr)", 0.02, 0.25, 0.08, 0.01, key="crc")
    slope_C = st.slider("Slope C (Degrees)", 0.0, 20.0, 0.0, 0.5, key="slc")
    speed_C = st.slider("Speed C (m/s)", 0.2, 3.0, 1.5, 0.1, key="spc")

# --- INITIAL SYSTEM CALCULATIONS & STRUCTURAL INTEGRATION ---
total_rover_start_weight_lbs = frame_weight + components_weight + battery_weight_lbs + fuel_weight_lbs

st.subheader("Chassis Design Envelope Evaluation")
if total_rover_start_weight_lbs > 175.0:
    st.error(f"❌ CRITICAL STRUCTURAL FAULT: Total initial weight ({total_rover_start_weight_lbs:.1f} lbs) violates constraints (> 175 lbs limit)!")
else:
    st.success(f"✅ STRUCTURAL SAFE: Total gross launch weight optimized at {total_rover_start_weight_lbs:.1f} lbs.")

# --- TRANSIENT TIME-SERIES SIMULATION ENGINE ENGINE ---
time_steps = np.arange(0, simulation_minutes + 1, 1)

# Allocation arrays tracking transient arrays
battery_soc_history = []
fuel_remaining_liters = []
power_demand_history = []
copper_loss_history = []
voltage_sag_history = []

# State initializations
current_battery_wh = usable_battery_wh
current_fuel_liters = fuel_tank_liters
bsfc_g_kwh = 380.0  # Brake Specific Fuel Consumption index baseline constant

for t in time_steps:
    # 1. Determine local environmental profile slice based on current timestep fraction
    if t <= (simulation_minutes * 0.33):
        c_rr = cr_A
        slope_deg = slope_A
        speed = speed_A
    elif t <= (simulation_minutes * 0.66):
        c_rr = cr_B
        slope_deg = slope_B
        speed = speed_B
    else:
        c_rr = cr_C
        slope_deg = slope_C
        speed = speed_C
        
    # Recalculate changing real-time structural payload mass as fuel gets consumed
    current_fuel_weight_lbs = current_fuel_liters * 1.63
    total_inst_weight_lbs = frame_weight + components_weight + battery_weight_lbs + current_fuel_weight_lbs
    total_inst_mass_kg = total_inst_weight_lbs * 0.45359237
    
    # 2. Physics Tractive System Forces
    slope_rad = np.radians(slope_deg)
    f_roll = total_inst_mass_kg * 9.81 * c_rr * np.cos(slope_rad)
    f_grade = total_inst_mass_kg * 9.81 * np.sin(slope_rad)
    tractive_force = f_roll + f_grade
    
    # 3. Apply Multi-Stage Powertrain Efficiencies (Transmission + Electrical)
    mechanical_power_wheels = tractive_force * speed
    electrical_power_demand = (mechanical_power_wheels / (motor_efficiency * transmission_efficiency)) + 20.0
    
    # 4. Advanced Circuit EE Calculations (Ohmic Loss & Voltage Drop)
    # Estimate standard working current based on power bus state variables
    approx_current = electrical_power_demand / pack_voltage
    
    # Calculate Copper Wiring Wire Losses and Battery Chemical Voltage Sag Drop
    wire_power_loss = (approx_current ** 2) * total_wire_resistance
    voltage_sag = approx_current * r_internal
    
    # Compound total demand reflecting non-ideal thermodynamic losses
    final_gross_power_demand = electrical_power_demand + wire_power_loss
    
    # 5. Hybrid Node Sizing Logic Flow Check
    if current_fuel_liters > 0 and generator_watts > 0:
        # Engine turns over: generates power, consumes localized gasoline reserves
        fuel_burn_g_per_min = (generator_watts / 1000.0) * bsfc_g_kwh / 60.0
        fuel_burn_liters_per_min = fuel_burn_g_per_min / 740.0 # Gas density conversion tracking metric
        current_fuel_liters = max(current_fuel_liters - fuel_burn_liters_per_min, 0.0)
        active_gen_watts = generator_watts
    else:
        active_gen_watts = 0.0 # Empty tank or engine generator hard-killed
        
    # Power Bus Balancing Node
    net_power_flow = active_gen_watts - final_gross_power_demand
    
    # Integrate energy change into battery storage array bank minute by minute
    energy_change_wh = (net_power_flow * (1.0 / 60.0))
    current_battery_wh = current_battery_wh + energy_change_wh
    
    # Clamp capacity variables bounds cleanly
    current_battery_wh = min(max(current_battery_wh, 0.0), usable_battery_wh)
    soc_percentage = (current_battery_wh / usable_battery_wh) * 100.0
    
    # Append state telemetry for downstream visualization processing
    battery_soc_history.append(soc_percentage)
    fuel_remaining_liters.append(current_fuel_liters)
    power_demand_history.append(final_gross_power_demand)
    copper_loss_history.append(wire_power_loss)
    voltage_sag_history.append(voltage_sag)

# --- VISUALIZATION DASHBOARD INTERFACES ---
st.subheader("📈 Real-Time Transient Mission Telemetry Graphs")

col_g1, col_g2 = st.columns(2)

with col_g1:
    fig_soc = go.Figure()
        fig_soc.add_trace(go.Scatter(x=time_steps, y=[f * (100.0/fuel_tank_liters) for f in fuel_remaining_liters], name="Fuel Level (% Tank Volume)", line=dict(color='#FFA500', width=3, dash='dash')))
    fig_soc.update_layout(
        title="Vehicle Storage Reservoirs Depletion Over Mission Timeline",
        xaxis_title="Simulation Time Elapsed (Minutes)",
        yaxis_title="Remaining Capacity (%)",
        yaxis=dict(range=[-5, 105]),
        template="plotly_dark",
        legend=dict(orientation="h", y=-0.2)
    )
    st.plotly_chart(fig_soc, use_container_width=True)

with col_g2:
    fig_pow = go.Figure()
    fig_pow.add_trace(go.Scatter(x=time_steps, y=power_demand_history, name="Gross System Power Demand (W)", line=dict(color='#FF3333', width=3)))
    fig_pow.add_trace(go.Scatter(x=time_steps, y=[generator_watts if f > 0 else 0 for f in fuel_remaining_liters], name="ICE Generator Output (W)", line=dict(color='#0068C9', width=2)))
    fig_pow.update_layout(
        title="Power Bus Load Matching Profile & Generation Balancing",
        xaxis_title="Simulation Time Elapsed (Minutes)",
        yaxis_title="Electrical Power (Watts)",
        template="plotly_dark",
        legend=dict(orientation="h", y=-0.2)
    )
    st.plotly_chart(fig_pow, use_container_width=True)

# --- ADVANCED METRIC DEEP-DIVE OVERVIEWS ---
st.subheader("🔬 Component Loss & Circuit Telemetry Overview")
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(label="Peak Total Power Draw", value=f"{max(power_demand_history):.1f} W")
with c2:
    st.metric(label="Worst-Case Cable Wire Loss", value=f"{max(copper_loss_history):.2f} W")
with c3:
    st.metric(label="Peak Battery Voltage Sag", value=f"{max(voltage_sag_history):.3f} V")
with c4:
    st.metric(label="Ending Onboard Fuel Volume", value=f"{fuel_remaining_liters[-1]:.2f} L")

st.info(
    f"**Electrical System-Level Analytical Note:** Notice how selection parameters dynamically affect electrical bounds. "
    f"Choosing a **12V bus** configuration causes system current loops to surge, spiking copper heating losses across your "
    f"wire run to a maximum value of **{max(copper_loss_history):.2f} Watts**. Upgrading hardware variables to a **24V topology** "
    f"will automatically drop internal losses, improving structural range without changing base fuel payloads."
)

   
