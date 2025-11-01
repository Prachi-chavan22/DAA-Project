import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import sys
import os
import pandas as pd

# ✅ Add backend folder to Python path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_path)

# ✅ Import backend modules
from backend.graph_simulation import IoTNetwork
from backend.routing_algorithms import RoutingEngine
from backend.energy_model import basic_energy_model

# ✅ Function to compare routing paths
def compare_routes(graph, dist_path, energy_path):
    dist_total = RoutingEngine.distance_cost(graph, dist_path)
    energy_total = RoutingEngine.energy_cost(graph, energy_path)

    dist_hops = len(dist_path) - 1
    energy_hops = len(energy_path) - 1

    energy_saved = dist_total - energy_total
    energy_saved_percent = (energy_saved / dist_total) * 100 if dist_total != 0 else 0

    data = {
        "Metric": ["Total Distance", "Total Energy Cost", "Hop Count", "Energy Saved (%)"],
        "Shortest Path": [
            str(dist_total),
            "-",
            str(dist_hops),
            "-"
        ],
        "Energy-Efficient Path": [
            "-",
            str(energy_total),
            str(energy_hops),
            f"{energy_saved_percent:.2f}%"
        ]
    }

    df = pd.DataFrame(data)
    return df


# ✅ FUNCTION TO DRAW GRAPH WITH ENERGY LABELS
def draw_network(graph, path=None):
    pos = nx.spring_layout(graph, seed=42)

    edge_x = []
    edge_y = []
    edge_labels_x = []
    edge_labels_y = []
    energy_text = []

    for u, v, data in graph.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

        # ✅ Label position (middle of edge)
        edge_labels_x.append((x0 + x1) / 2)
        edge_labels_y.append((y0 + y1) / 2)
        energy_text.append(f"{data['energy_cost']}")

    # ✅ Edges
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1),
        hoverinfo='none',
        mode='lines'
    )

    # ✅ Edge energy labels
    label_trace = go.Scatter(
        x=edge_labels_x,
        y=edge_labels_y,
        mode='text',
        text=energy_text,
        textposition="top center",
        hoverinfo="none"
    )

    # ✅ Nodes
    node_x = []
    node_y = []
    text_info = []
    for node in graph.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        text_info.append(f"Node: {node}")

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=[str(n) for n in graph.nodes()],
        textposition="top center",
        marker=dict(size=18),
        hovertext=text_info
    )

    # ✅ Highlight path
    if path:
        px = []
        py = []
        for u, v in zip(path, path[1:]):
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            px.extend([x0, x1, None])
            py.extend([y0, y1, None])

        path_trace = go.Scatter(
            x=px, y=py,
            mode='lines',
            line=dict(width=4),
            hoverinfo='none'
        )
        return [edge_trace, path_trace, node_trace, label_trace]

    return [edge_trace, node_trace, label_trace]


# ✅ STREAMLIT PAGE SETTINGS
st.set_page_config(
    page_title="IoT Energy Efficient Routing",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}  # ✅ REMOVE 3 DOT MENU + DEPLOY BUTTON
)

st.title("🌐 Energy-Efficient Data Routing in IoT Networks")


# ✅ Sidebar Settings
st.sidebar.header("⚙️ Simulation Settings")
num_nodes = st.sidebar.slider("Number of IoT Devices", 5, 25, 10)

if st.sidebar.button("Generate Network"):
    st.session_state['network'] = IoTNetwork(num_nodes=num_nodes)
    st.session_state['network'].assign_energy_costs(basic_energy_model)
    st.success("✅ New IoT Network Generated!")


# ✅ MAIN UI
if 'network' in st.session_state:
    graph = st.session_state['network'].graph

    st.subheader("📡 Network Visualization")

    path = None  # default

    col1, col2 = st.columns(2)
    with col1:
        source = st.selectbox("Select Source Node", list(graph.nodes()))
    with col2:
        target = st.selectbox("Select Target Node", list(graph.nodes()))

    # ✅ Shortest Distance Routing
    if st.button("Run Shortest Distance Routing"):
        try:
            path = RoutingEngine.shortest_path_distance(graph, source, target)
            st.info(f"📌 Shortest Path: {path}")
            st.write(f"✅ Total Distance = {RoutingEngine.distance_cost(graph, path)}")
        except nx.NetworkXNoPath:
            st.error("❌ No path exists")

    # ✅ Energy Efficient Routing
    if st.button("Run Energy Efficient Routing"):
        try:
            path = RoutingEngine.shortest_path_energy(graph, source, target)
            st.success(f"✅ Energy Efficient Path: {path}")
            st.write(f"⚡ Total Energy Cost = {RoutingEngine.energy_cost(graph, path)}")
        except nx.NetworkXNoPath:
            st.error("❌ No path exists")

    # ✅ Comparison Table
    if st.button("Compare Routes"):
        try:
            dist_path = RoutingEngine.shortest_path_distance(graph, source, target)
            energy_path = RoutingEngine.shortest_path_energy(graph, source, target)

            df = compare_routes(graph, dist_path, energy_path)
            st.subheader("📊 Routing Comparison")
            st.table(df)

        except nx.NetworkXNoPath:
            st.error("❌ No path exists")

    # ✅ Draw graph
    traces = draw_network(graph, path)
    fig = go.Figure(data=traces)

    # ✅ Limit toolbar to only download + fullscreen
    fig.update_layout(
        showlegend=False,
        height=600,
        modebar={
            "remove": [
                "zoom", "pan", "select", "lasso2d",
                "zoomIn2d", "zoomOut2d", "autoScale2d",
                "hoverClosestCartesian", "hoverCompareCartesian"
            ]
        }
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("⚠️ Click 'Generate Network' to start.")
