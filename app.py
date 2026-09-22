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
        range=[0, 24]
    ),
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
