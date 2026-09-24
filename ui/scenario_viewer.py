import json
import os
from pathlib import Path
import streamlit as st
import plotly.graph_objects as go

SCENARIOS_DIR = Path(__file__).parent.parent / "data" / "scenarios"

ZONE_LAYOUT = {
    "north_bank":     {"x": 1, "y": 3, "label": "North Bank",  "color": "#1a3a5c"},
    "south_bank":     {"x": 1, "y": 1, "label": "South Bank",  "color": "#1a3a5c"},
    "reserve":        {"x": 3, "y": 2, "label": "Reserve",     "color": "#2d4a1e"},
    "rear":           {"x": 4, "y": 2, "label": "Rear",        "color": "#3a3a1a"},
    "classified":     {"x": 3, "y": 3, "label": "Classified",  "color": "#4a1a1a"},
}

UNIT_ICONS = {
    "armor":     "🪖",
    "infantry":  "🏃",
    "artillery": "💣",
    "special":   "🔒",
}

ROLE_COLORS = {
    "analyst":   "#f0c040",
    "planner":   "#40a0f0",
    "commander": "#f04040",
}


def load_scenario(path: Path) -> dict:
    return json.loads(path.read_text())


def render_battlefield(scenario: dict, user_role: str):
    units = scenario["units"]
    role_clearance = {"analyst": 1, "planner": 2, "commander": 3}
    role_min = {"analyst": 1, "planner": 2, "commander": 3}
    clearance = role_clearance.get(user_role, 1)

    # Group units by zone
    zones: dict[str, list] = {}
    for u in units:
        zone = u["location"]
        zones.setdefault(zone, []).append(u)

    fig = go.Figure()

    # Draw zone backgrounds
    for zone, props in ZONE_LAYOUT.items():
        fig.add_shape(
            type="rect",
            x0=props["x"] - 0.45, x1=props["x"] + 0.45,
            y0=props["y"] - 0.45, y1=props["y"] + 0.45,
            fillcolor=props["color"], opacity=0.4,
            line=dict(color="white", width=1),
        )
        fig.add_annotation(
            x=props["x"], y=props["y"] + 0.38,
            text=f"<b>{props['label']}</b>",
            showarrow=False, font=dict(color="white", size=11),
        )

    # Draw river
    fig.add_shape(
        type="rect",
        x0=0.0, x1=2.5, y0=1.9, y1=2.1,
        fillcolor="#1e6091", opacity=0.7,
        line=dict(color="#5bc0eb", width=2),
    )
    fig.add_annotation(
        x=1.25, y=2.0, text="〰 RIVER 〰",
        showarrow=False, font=dict(color="#5bc0eb", size=12),
    )

    # Draw units
    for zone, unit_list in zones.items():
        if zone not in ZONE_LAYOUT:
            continue
        zx = ZONE_LAYOUT[zone]["x"]
        zy = ZONE_LAYOUT[zone]["y"]

        for i, unit in enumerate(unit_list):
            min_role_clearance = role_min.get(unit.get("min_role", "analyst"), 1)
            visible = clearance >= min_role_clearance

            offset_x = (i - len(unit_list) / 2) * 0.2
            icon = UNIT_ICONS.get(unit["type"], "●")
            color = "#888" if not visible else ("#4caf50" if unit["available"] else "#f44336")
            label = unit["name"] if visible else "[ CLASSIFIED ]"
            strength = f"Str: {unit['strength']}" if visible else ""

            fig.add_trace(go.Scatter(
                x=[zx + offset_x], y=[zy - 0.1],
                mode="markers+text",
                marker=dict(size=28, color=color, symbol="square"),
                text=[icon],
                textfont=dict(size=16),
                textposition="middle center",
                hovertemplate=(
                    f"<b>{label}</b><br>"
                    f"Type: {unit['type']}<br>"
                    f"{strength}<br>"
                    f"Available: {unit['available']}<br>"
                    f"Min role: {unit.get('min_role','analyst')}"
                    "<extra></extra>"
                ),
                showlegend=False,
            ))

            fig.add_annotation(
                x=zx + offset_x, y=zy - 0.28,
                text=f"<span style='font-size:9px'>{label[:18]}</span>",
                showarrow=False, font=dict(color="white", size=8),
            )

    fig.update_layout(
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        xaxis=dict(visible=False, range=[-0.1, 5.2]),
        yaxis=dict(visible=False, range=[0.4, 3.7]),
        margin=dict(l=0, r=0, t=10, b=0),
        height=420,
    )
    return fig


def render_constraints(scenario: dict):
    constraints = scenario.get("constraints", [])
    for c in constraints:
        icon = {"force_limit": "⚠️", "restricted_zone": "🚫", "requires_confirmation": "🔐"}.get(
            c["constraint_type"], "📋"
        )
        st.markdown(f"{icon} **{c['id']}** — {c['text']}  \n`{c['source']}`")


def render_unit_table(scenario: dict, user_role: str):
    role_clearance = {"analyst": 1, "planner": 2, "commander": 3}
    clearance = role_clearance.get(user_role, 1)
    role_min = {"analyst": 1, "planner": 2, "commander": 3}

    rows = []
    for u in scenario["units"]:
        visible = clearance >= role_min.get(u.get("min_role", "analyst"), 1)
        rows.append({
            "Unit": u["name"] if visible else "[ CLASSIFIED ]",
            "Type": u["type"] if visible else "—",
            "Strength": u["strength"] if visible else "—",
            "Location": u["location"],
            "Available": "✅" if u["available"] else "❌",
            "Min Role": u.get("min_role", "analyst"),
            "Visible": "👁" if visible else "🔒",
        })
    st.dataframe(rows, use_container_width=True)


# ── App ──────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="ORA Scenario Viewer", layout="wide", page_icon="🗺️")

st.title("🗺️ ORA Scenario Viewer")

col_s, col_r = st.columns([2, 1])

with col_s:
    scenario_files = sorted(SCENARIOS_DIR.glob("*.json"))
    selected = st.selectbox(
        "Scenario",
        scenario_files,
        format_func=lambda p: p.stem,
    )

with col_r:
    user_role = st.selectbox("Your role", ["analyst", "planner", "commander"])

scenario = load_scenario(selected)

st.markdown(f"**Objective:** {scenario.get('objective', '—')}")
st.markdown(f"**Blue force:** {scenario.get('blue_force_strength', '—')} &nbsp;|&nbsp; "
            f"**Time window:** {scenario.get('time_window_hours', '—')}h")

st.plotly_chart(render_battlefield(scenario, user_role), use_container_width=True)

tab1, tab2 = st.tabs(["Units", "Constraints"])

with tab1:
    render_unit_table(scenario, user_role)

with tab2:
    render_constraints(scenario)
