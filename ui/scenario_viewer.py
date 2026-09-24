import json
import math
import numpy as np
from pathlib import Path
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

SCENARIOS_DIR = Path(__file__).parent.parent / "data" / "scenarios"

THREAT_COLORS = {"critical": "#ff2244", "high": "#ff8800", "medium": "#ffcc00", "low": "#88ccff"}
LAYER_COLORS  = {
    "exo-atmospheric": "#cc44ff",
    "endo-atmospheric": "#4466ff",
    "upper-tier":       "#44aaff",
    "medium-high":      "#44ddaa",
    "short-range":      "#44ff88",
}
PRIORITY_SIZE = {"critical": 14, "high": 10, "medium": 8, "low": 6}

WEAPON_ICONS = {"ballistic_missile": "🚀", "hypersonic": "⚡", "cruise_missile": "✈️",
                "drone": "🛸", "rocket": "💥", "mortar": "💣"}

CSS = """
<style>
[data-testid="stAppViewContainer"] { background: #0d1117; color: #e6edf3; }
[data-testid="stSidebar"]          { background: #161b22; }
.stTabs [data-baseweb="tab"]       { background: #161b22; color: #8b949e; }
.stTabs [aria-selected="true"]     { background: #1f2937; color: #e6edf3; border-bottom: 2px solid #58a6ff; }
.metric-card { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:14px; margin:6px 0; }
.threat-badge { display:inline-block; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:bold; }
div[data-testid="metric-container"] { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:10px; }
</style>
"""


def load_scenarios() -> dict[str, dict]:
    out = {}
    for p in sorted(SCENARIOS_DIR.glob("*.json")):
        d = json.loads(p.read_text())
        out[p.stem] = d
    return out


def circle_latlons(lat: float, lon: float, radius_km: float, n: int = 60):
    R = 6371.0
    lats, lons = [], []
    for i in range(n + 1):
        angle = 2 * math.pi * i / n
        d = radius_km / R
        lat2 = math.degrees(math.asin(
            math.sin(math.radians(lat)) * math.cos(d) +
            math.cos(math.radians(lat)) * math.sin(d) * math.cos(angle)
        ))
        lon2 = lon + math.degrees(math.atan2(
            math.sin(angle) * math.sin(d) * math.cos(math.radians(lat)),
            math.cos(d) - math.sin(math.radians(lat)) * math.sin(math.radians(lat2))
        ))
        lats.append(lat2)
        lons.append(lon2)
    return lats, lons


def build_map(scenario: dict, show_coverage: bool, show_threats: bool, show_ndz: bool) -> go.Figure:
    fig = go.Figure()
    defender = scenario["defender"]

    # ── Key assets ────────────────────────────────────────────────────────────
    assets = defender["key_assets"]
    fig.add_trace(go.Scattergeo(
        lat=[a["lat"] for a in assets],
        lon=[a["lon"] for a in assets],
        mode="markers+text",
        marker=dict(
            size=[PRIORITY_SIZE.get(a["priority"], 8) for a in assets],
            color="#58a6ff", symbol="circle",
            line=dict(color="#1f6feb", width=1),
        ),
        text=[a["name"] for a in assets],
        textposition="top right",
        textfont=dict(color="#58a6ff", size=10),
        hovertemplate="<b>%{text}</b><br>Priority: %{customdata}<extra></extra>",
        customdata=[a["priority"] for a in assets],
        name="Protected Assets",
        showlegend=True,
    ))

    # ── Attackers + vectors ───────────────────────────────────────────────────
    if show_threats:
        for atk in scenario["attackers"]:
            color = THREAT_COLORS.get(atk["threat_level"], "#ff8800")
            # Arrow line from attacker to defender
            fig.add_trace(go.Scattergeo(
                lat=[atk["lat"], defender["lat"]],
                lon=[atk["lon"], defender["lon"]],
                mode="lines",
                line=dict(color=color, width=1.5, dash="dash"),
                hoverinfo="skip", showlegend=False,
            ))
            # Attacker marker
            total_weapons = sum(w["count"] for w in atk["weapons"])
            fig.add_trace(go.Scattergeo(
                lat=[atk["lat"]], lon=[atk["lon"]],
                mode="markers+text",
                marker=dict(size=16, color=color, symbol="triangle-up",
                            line=dict(color="white", width=1)),
                text=[atk["name"]],
                textposition="bottom center",
                textfont=dict(color=color, size=10),
                hovertemplate=(
                    f"<b>{atk['name']}</b><br>"
                    f"Threat: {atk['threat_level']}<br>"
                    f"Weapon types: {len(atk['weapons'])}<br>"
                    f"Total munitions: {total_weapons:,}"
                    "<extra></extra>"
                ),
                name=atk["name"], showlegend=True,
            ))

    # ── No-deploy zones ───────────────────────────────────────────────────────
    if show_ndz:
        for ndz in scenario["no_deploy_zones"]:
            lats, lons = circle_latlons(ndz["lat"], ndz["lon"], ndz["radius_km"])
            fig.add_trace(go.Scattergeo(
                lat=lats, lon=lons, mode="lines",
                line=dict(color="#ff6b35", width=1.5, dash="dot"),
                fill="toself", fillcolor="rgba(255,107,53,0.12)",
                hoverinfo="skip", showlegend=False,
            ))
            fig.add_trace(go.Scattergeo(
                lat=[ndz["lat"]], lon=[ndz["lon"]],
                mode="markers+text",
                marker=dict(size=8, color="#ff6b35", symbol="x"),
                text=[ndz["name"]],
                textposition="top left",
                textfont=dict(color="#ff6b35", size=9),
                hovertemplate=f"<b>{ndz['name']}</b><br>{ndz['reason']}<extra></extra>",
                showlegend=False,
            ))

    # ── Defense coverage ──────────────────────────────────────────────────────
    if show_coverage:
        for dep in scenario.get("deployments", []):
            sys_def = next((s for s in scenario["defense_systems"] if s["id"] == dep["system_id"]), None)
            if not sys_def:
                continue
            color = LAYER_COLORS.get(sys_def["layer"], "#44ff88")
            lats, lons = circle_latlons(dep["lat"], dep["lon"], sys_def["range_km"])
            fig.add_trace(go.Scattergeo(
                lat=lats, lon=lons, mode="lines",
                line=dict(color=color, width=1),
                fill="toself", fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:],16)},0.08)",
                hoverinfo="skip", showlegend=False,
            ))
            fig.add_trace(go.Scattergeo(
                lat=[dep["lat"]], lon=[dep["lon"]],
                mode="markers+text",
                marker=dict(size=12, color=color, symbol="square"),
                text=[sys_def["name"]],
                textposition="top right",
                textfont=dict(color=color, size=9),
                hovertemplate=f"<b>{sys_def['name']}</b><br>Layer: {sys_def['layer']}<br>Range: {sys_def['range_km']} km<extra></extra>",
                showlegend=False,
            ))

    fig.update_layout(
        geo=dict(
            showland=True, landcolor="#1c2333",
            showocean=True, oceancolor="#0d1b2a",
            showcoastlines=True, coastlinecolor="#30363d",
            showcountries=True, countrycolor="#30363d",
            showframe=False,
            center=dict(lat=30.0, lon=39.0),
            projection_type="natural earth",
            lonaxis_range=[28, 60],
            lataxis_range=[12, 38],
        ),
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        margin=dict(l=0, r=0, t=0, b=0),
        height=520,
        legend=dict(bgcolor="#161b22", font=dict(color="#e6edf3", size=10),
                    bordercolor="#30363d", borderwidth=1),
    )
    return fig


def render_threats_tab(scenario: dict):
    for atk in scenario["attackers"]:
        color = THREAT_COLORS.get(atk["threat_level"], "#888")
        st.markdown(f"""
<div class="metric-card">
<h3 style="color:{color};margin:0">▲ {atk['name']}
  <span class="threat-badge" style="background:{color}22;color:{color};margin-left:8px">
    {atk['threat_level'].upper()}
  </span>
</h3>
</div>""", unsafe_allow_html=True)

        rows = []
        for w in atk["weapons"]:
            rows.append({
                "": WEAPON_ICONS.get(w["type"], "•"),
                "Name": w["name"],
                "Type": w["type"].replace("_", " "),
                "Range (km)": w["range_km"],
                "Speed (Mach)": w["speed_mach"],
                "Alt max (km)": w["altitude_max_km"],
                "RCS (m²)": w["rcs_sqm"],
                "Payload (kg)": w["payload_kg"],
                "CEP (m)": w["cep_m"],
                "Count": f"{w['count']:,}",
                "Threat": w["threat_level"],
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True,
                     column_config={"Threat": st.column_config.TextColumn(
                         width="small")})
        st.caption(f"ℹ️  " + " · ".join(w["notes"] for w in atk["weapons"]))
        st.divider()


def render_defense_tab(scenario: dict):
    deployed_ids = {d["system_id"] for d in scenario.get("deployments", [])}

    cols = st.columns(2)
    for i, sys in enumerate(scenario["defense_systems"]):
        color = LAYER_COLORS.get(sys["layer"], "#44ff88")
        deployed = sum(1 for d in scenario.get("deployments", []) if d["system_id"] == sys["id"])
        available = sys["batteries_available"] - deployed

        with cols[i % 2]:
            st.markdown(f"""
<div class="metric-card" style="border-left:3px solid {color}">
<h4 style="color:{color};margin:0 0 8px 0">■ {sys['name']}</h4>
<div style="color:#8b949e;font-size:12px;margin-bottom:8px">{sys['layer'].upper()} LAYER</div>
<table style="font-size:12px;width:100%;border-collapse:collapse">
  <tr><td style="color:#8b949e;padding:2px 8px 2px 0">Range</td><td><b>{sys['range_km']} km</b></td>
      <td style="color:#8b949e;padding:2px 8px 2px 12px">Altitude</td><td><b>{sys['altitude_min_km']}–{sys['altitude_max_km']} km</b></td></tr>
  <tr><td style="color:#8b949e;padding:2px 8px 2px 0">P(intercept)</td><td><b>{int(sys['intercept_probability']*100)}%</b></td>
      <td style="color:#8b949e;padding:2px 8px 2px 12px">Reload</td><td><b>{sys['reload_time_s']}s</b></td></tr>
  <tr><td style="color:#8b949e;padding:2px 8px 2px 0">Cost/shot</td><td><b>${sys['cost_per_intercept_musd']}M</b></td>
      <td style="color:#8b949e;padding:2px 8px 2px 12px">Batteries</td>
      <td><b style="color:#44ff88">{deployed} deployed</b> / {sys['batteries_available']} total</td></tr>
</table>
<div style="margin-top:8px;font-size:11px;color:#8b949e">
  Intercepts: {' · '.join(f'<span style="color:{color}">{t.replace("_"," ")}</span>' for t in sys['intercepts'])}
</div>
<div style="margin-top:6px;font-size:11px;color:#6e7681;font-style:italic">{sys['notes']}</div>
</div>""", unsafe_allow_html=True)


def render_ndz_tab(scenario: dict):
    TYPE_ICONS = {"religious_heritage": "⛪", "aviation": "✈️",
                  "population_density": "🏙️", "heritage_site": "🏛️", "border_zone": "🚧"}
    for ndz in scenario["no_deploy_zones"]:
        icon = TYPE_ICONS.get(ndz["type"], "🚫")
        st.markdown(f"""
<div class="metric-card" style="border-left:3px solid #ff6b35">
<b>{icon} {ndz['name']}</b>
<span style="font-size:11px;color:#ff6b35;margin-left:8px">{ndz['type'].replace('_',' ').upper()}</span><br>
<span style="font-size:12px;color:#8b949e">Exclusion radius: {ndz['radius_km']} km &nbsp;|&nbsp; {ndz['lat']}°N {ndz['lon']}°E</span><br>
<span style="font-size:12px;color:#6e7681">{ndz['reason']}</span>
</div>""", unsafe_allow_html=True)


def render_summary(scenario: dict):
    total_munitions = sum(w["count"] for a in scenario["attackers"] for w in a["weapons"])
    total_batteries = sum(s["batteries_available"] for s in scenario["defense_systems"])
    deployed = len(scenario.get("deployments", []))
    attackers = len(scenario["attackers"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Attacking forces", attackers)
    c2.metric("Total munitions", f"{total_munitions:,}")
    c3.metric("Defense batteries", total_batteries)
    c4.metric("Deployed", deployed, delta=f"{total_batteries - deployed} available")


# ── App ───────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="ORA Air Defense Planner", layout="wide", page_icon="🛡️")
st.markdown(CSS, unsafe_allow_html=True)

scenarios = load_scenarios()
air_defense = {k: v for k, v in scenarios.items() if v.get("type") == "air_defense"}

with st.sidebar:
    st.markdown("## 🛡️ Air Defense Planner")
    if not air_defense:
        st.error("No air defense scenarios found.")
        st.stop()

    selected_id = st.selectbox("Scenario", list(air_defense.keys()),
                               format_func=lambda k: air_defense[k]["name"])
    scenario = air_defense[selected_id]

    st.divider()
    st.markdown("**Map layers**")
    show_threats  = st.toggle("Threat vectors",   value=True)
    show_coverage = st.toggle("Defense coverage", value=True)
    show_ndz      = st.toggle("No-deploy zones",  value=True)

st.markdown(f"# 🛡️ {scenario['name']}")
st.caption(f"Defending: **{scenario['defender']['name']}**  |  "
           f"Scenario: `{scenario['scenario_id']}`  |  v{scenario['version']}")

render_summary(scenario)

tab_map, tab_threats, tab_defense, tab_ndz = st.tabs(
    ["🗺️  Map", "⚠️  Threats & Weapons", "🛡️  Defense Systems", "🚫  No-Deploy Zones"]
)

with tab_map:
    st.plotly_chart(build_map(scenario, show_coverage, show_threats, show_ndz),
                    use_container_width=True)
    st.caption("🔵 Protected assets  ·  ▲ Attackers  ·  🟠 No-deploy zones  ·  ■ Deployed systems (coverage circles)")

with tab_threats:
    render_threats_tab(scenario)

with tab_defense:
    render_defense_tab(scenario)

with tab_ndz:
    render_ndz_tab(scenario)
