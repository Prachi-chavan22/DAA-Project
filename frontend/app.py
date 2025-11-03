import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
import sys, os
import pandas as pd

# ✅ Add backend path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.append(root_path)

# ✅ Import backend logic
from backend.graph_simulation import IoTNetwork
from backend.routing_algorithms import RoutingEngine
from backend.energy_model import advanced_energy_model


# --------------------------------------------------------
# ✅ Packet Size Graph
# --------------------------------------------------------
def packet_size_energy_curve(distance):
    sizes = [1, 5, 10]
    labels = ["Small", "Medium", "Large"]
    energy_values = [advanced_energy_model(distance, s) for s in sizes]

    df = pd.DataFrame({"Packet Size": labels, "Energy Cost": energy_values})

    fig = px.line(
        df,
        x="Packet Size",
        y="Energy Cost",
        markers=True,
        title=f"Energy Cost vs Packet Size (Distance = {distance})"
    )
    fig.update_layout(height=300)
    return fig


# --------------------------------------------------------
# ✅ Battery History Helpers
# --------------------------------------------------------
def _init_battery_history():
    if 'battery_history' not in st.session_state:
        st.session_state['battery_history'] = {}
    if 'hist_steps' not in st.session_state:
        st.session_state['hist_steps'] = 0
    if 'last_path_nodes' not in st.session_state:
        st.session_state['last_path_nodes'] = []


def update_battery_history(graph, path):
    _init_battery_history()
    st.session_state['last_path_nodes'] = list(path)

    for node in path:
        curr_energy = graph.nodes[node].get('energy', 0)
        if node not in st.session_state['battery_history']:
            st.session_state['battery_history'][node] = [None] * st.session_state['hist_steps']
        st.session_state['battery_history'][node].append(curr_energy)

    for node, history in st.session_state['battery_history'].items():
        if node not in path:
            history.append(None)

    st.session_state['hist_steps'] += 1


def plot_battery_history_for_last_path():
    _init_battery_history()
    last_nodes = st.session_state['last_path_nodes']

    if not last_nodes:
        st.info("Run a route to display battery history.")
        return

    steps = st.session_state['hist_steps']
    history = st.session_state['battery_history']

    df = pd.DataFrame(index=list(range(steps)))

    for node in last_nodes:
        hist = history.get(node, [])
        if len(hist) < steps:
            hist += [None] * (steps - len(hist))
        df[f"Node {node}"] = hist

    df = df.dropna(how='all')
    if df.empty:
        st.info("No battery values recorded yet.")
        return

    df_long = df.reset_index().melt(id_vars='index', var_name='Node', value_name='Battery')

    fig = px.line(
        df_long,
        x='index',
        y='Battery',
        color='Node',
        markers=True,
        title="Battery Usage History (Last Routed Path)"
    )
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)


# --------------------------------------------------------
# ✅ Routing Comparison Table
# --------------------------------------------------------
def compare_routes(graph, dist_path, energy_path):
    dist_energy = RoutingEngine.energy_cost(graph, dist_path)
    e_energy = RoutingEngine.energy_cost(graph, energy_path)

    saved = dist_energy - e_energy
    saved_percent = (saved / dist_energy * 100) if dist_energy > 0 else 0

    df = pd.DataFrame({
        "Metric": [
            "Shortest Path Distance",
            "Energy (Shortest Path)",
            "Energy (Energy Efficient)",
            "Energy Saved (%)"
        ],
        "Value": [
            f"{RoutingEngine.distance_cost(graph, dist_path):.2f}",
            f"{dist_energy:.2f}",
            f"{e_energy:.2f}",
            f"{saved_percent:.2f}%"
        ]
    })
    return df


# --------------------------------------------------------
# ✅ Draw IoT Network Graph
# --------------------------------------------------------
def draw_network(graph, path=None):
    pos = nx.spring_layout(graph, seed=42)

    edge_x, edge_y = [], []
    label_x, label_y, label_text = [], [], []

    for u, v, data in graph.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]

        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

        label_x.append((x0 + x1) / 2)
        label_y.append((y0 + y1) / 2)
        label_text.append(f"{data['energy_cost']:.2f}")

    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(width=1))
    label_trace = go.Scatter(x=label_x, y=label_y, mode="text", text=label_text)

    node_x, node_y, node_colors, hover = [], [], [], []

    for node in graph.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        e = graph.nodes[node]["energy"]
        hover.append(f"Node {node} | Energy: {e}")

        if e > 60:
            node_colors.append("green")
        elif e > 30:
            node_colors.append("yellow")
        elif e > 0:
            node_colors.append("red")
        else:
            node_colors.append("black")

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=list(graph.nodes()),
        textposition="top center",
        marker=dict(size=18, color=node_colors),
        hovertext=hover
    )

    traces = [edge_trace, node_trace, label_trace]

    if path:
        px, py = [], []
        for u, v in zip(path, path[1:]):
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            px.extend([x0, x1, None])
            py.extend([y0, y1, None])

        path_trace = go.Scatter(x=px, y=py, mode="lines", line=dict(width=4))
        traces.insert(1, path_trace)

    return traces


# --------------------------------------------------------
# ✅ STREAMLIT MAIN UI
# --------------------------------------------------------
st.set_page_config(page_title="IoT Routing", layout="wide")
st.title("🌐 Energy-Efficient Data Routing in IoT Networks")

st.sidebar.header("⚙️ Configuration")
num_nodes = st.sidebar.slider("Total IoT Devices", 5, 25, 10)
pkt_label = st.sidebar.radio("Packet Size", ("Small", "Medium", "Large"))
pkt_map = {"Small": 1, "Medium": 5, "Large": 10}
packet_size = pkt_map[pkt_label]


# ✅ Generate Network
if st.sidebar.button("Generate Network"):
    st.session_state['network'] = IoTNetwork(num_nodes)
    st.session_state['network'].assign_energy_costs(advanced_energy_model, packet_size)

    _init_battery_history()

    # record initial energy snapshot
    for node in st.session_state['network'].graph.nodes():
        st.session_state['battery_history'][node] = [
            st.session_state['network'].graph.nodes[node]['energy']
        ]

    st.session_state['hist_steps'] = 1
    st.success("✅ Network Successfully Generated!")


# --------------------------------------------------------
# ✅ MAIN SCREEN AFTER NETWORK CREATION
# --------------------------------------------------------
if 'network' in st.session_state:

    graph = st.session_state['network'].graph

    st.subheader("📡 IoT Network Graph")

    col1, col2 = st.columns(2)
    source = col1.selectbox("Source", list(graph.nodes()))
    target = col2.selectbox("Target", list(graph.nodes()))

    path_draw = None

    left, right = st.columns(2)

    # ✅ Shortest Distance Routing
    with left:
        if st.button("Run Shortest Distance Routing"):
            try:
                path = RoutingEngine.shortest_path_distance(graph, source, target)
                RoutingEngine.apply_battery_drain(graph, path, packet_size)
                st.session_state['network'].assign_energy_costs(advanced_energy_model, packet_size)
                update_battery_history(graph, path)

                path_draw = path
                st.info(f"📌 Path: {path}")
            except:
                st.error("❌ No path found")

    # ✅ Energy Efficient Routing
    with left:
        if st.button("Run Energy Efficient Routing"):
            try:
                path = RoutingEngine.shortest_path_energy(graph, source, target)
                RoutingEngine.apply_battery_drain(graph, path, packet_size)
                st.session_state['network'].assign_energy_costs(advanced_energy_model, packet_size)
                update_battery_history(graph, path)

                path_draw = path
                st.success(f"✅ Energy Path: {path}")
            except:
                st.error("❌ No path found")

    # ✅ Compare Routes
    with right:
        if st.button("Compare Paths"):
            try:
                dpath = RoutingEngine.shortest_path_distance(graph, source, target)
                epath = RoutingEngine.shortest_path_energy(graph, source, target)
                st.table(compare_routes(graph, dpath, epath))
            except:
                st.error("Unable to compare")

    # ✅ Random Node Failure
    with right:
        if st.button("Simulate Node Failure"):
            fail = st.session_state['network'].fail_random_node()
            st.session_state['network'].assign_energy_costs(advanced_energy_model, packet_size)
            st.error(f"💀 Node {fail} Failed!" if fail is not None else "No alive node left")

    # ✅ Draw Final Network Graph (with removed zoom/pan + no traces)
    traces = draw_network(graph, path_draw)
    fig = go.Figure(data=traces)
    fig.update_layout(
        height=600,
        showlegend=False,
        modebar_remove=[
            "zoom", "pan", "zoomIn2d", "zoomOut2d",
            "autoScale2d", "resetScale2d",
            "select2d", "lasso2d"
        ]
    )
    st.plotly_chart(fig, use_container_width=True)

    # ✅ Battery History Graph
    st.subheader("📉 Battery History (Nodes in Last Path)")
    plot_battery_history_for_last_path()

    # ✅ Packet Size Graph (always last)
    st.subheader("📈 Packet Size vs Energy Cost")
    demo_dist = st.slider("Pick Distance", 1, 20, 10)
    fig2 = packet_size_energy_curve(demo_dist)
    fig2.update_layout(
        showlegend=False,
        modebar_remove=[
            "zoom", "pan", "zoomIn2d", "zoomOut2d",
            "autoScale2d", "resetScale2d",
            "select2d", "lasso2d"
        ]
    )
    st.plotly_chart(fig2, use_container_width=True)


    # ✅ Sidebar Summary
    alive = sum(1 for _, d in graph.nodes(data=True) if d['energy'] > 0)
    dead = len(graph.nodes) - alive

    st.sidebar.markdown("### 📊 Network Status")
    st.sidebar.write(f"🟢 Alive Nodes: {alive}")
    st.sidebar.write(f"⚫ Dead Nodes: {dead}")

else:
    st.warning("⚠️ Please generate a network to start.")
