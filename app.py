# --- ADVANCED MISSION CAPABILITY PREDICTOR PANEL ---
st.subheader("⏱️ Reliable Mission Performance Sizing Predictions")

average_demand_watts = np.mean(power_demand_history)

# 1. Calculate precise battery runtime under current loading parameters
if average_demand_watts > generator_watts:
    net_battery_drain_watts = average_demand_watts - generator_watts
    exact_battery_runtime_mins = (usable_battery_wh / net_battery_drain_watts) * 60.0
    battery_status_msg = f"⚠️ **Battery Depletion Warning:** Continuous deficit draw active. Reserves will drain in **{exact_battery_runtime_mins:.1f} minutes** if running without generator support."
else:
    exact_battery_runtime_mins = float('inf')
    battery_status_msg = "🔋 **Battery State Stable:** Onboard generation meets or exceeds mechanical traction loads. Battery reserves preserved."

# 2. Calculate runtime provided strictly by a single fuel tank load
fuel_burn_g_per_min_max = (generator_watts / 1000.0) * bsfc_g_kwh / 60.0
fuel_burn_liters_per_min_max = fuel_burn_g_per_min_max / 740.0

if fuel_burn_liters_per_min_max > 0:
    exact_fuel_runtime_mins = fuel_tank_liters / fuel_burn_liters_per_min_max
    fuel_status_msg = f"⛽ **Fuel Tank Range:** Your {fuel_tank_liters:.1f}L fuel capacity yields exactly **{exact_fuel_runtime_mins:.1f} minutes** of continuous generator operational runtime."
else:
    exact_fuel_runtime_mins = 0.0
    fuel_status_msg = "🚫 **Generator Inactive:** No fuel consumption active (Generator capacity set to 0W)."

# Display crisp status alerts to the user
calc_col1, calc_col2 = st.columns(2)
with calc_col1:
    st.info(fuel_status_msg)
with calc_col2:
    if exact_battery_runtime_mins == float('inf'):
        st.success(battery_status_msg)
    else:
        st.error(battery_status_msg)
