import networkx as nx

class RoutingEngine:

    @staticmethod
    def _alive_subgraph(graph):
        """
        Return a copy of the graph with nodes of energy <= 0 removed.
        """
        alive_graph = graph.copy()
        for node, data in list(alive_graph.nodes(data=True)):
            if data.get('energy', 0) <= 0:
                # remove dead or zero-energy nodes
                alive_graph.remove_node(node)
        return alive_graph

    @staticmethod
    def shortest_path_distance(graph, source, target):
        """
        Shortest path computed by 'distance' weight while avoiding dead nodes.
        Raises nx.NetworkXNoPath if no route exists.
        """
        alive_graph = RoutingEngine._alive_subgraph(graph)
        try:
            return nx.shortest_path(alive_graph, source=source, target=target, weight='distance')
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            raise nx.NetworkXNoPath("No path exists (distance)")

    @staticmethod
    def shortest_path_energy(graph, source, target):
        """
        Energy-efficient routing using 'energy_cost' weight while avoiding dead nodes.
        Raises nx.NetworkXNoPath if no route exists.
        """
        alive_graph = RoutingEngine._alive_subgraph(graph)
        try:
            return nx.shortest_path(alive_graph, source=source, target=target, weight='energy_cost')
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            raise nx.NetworkXNoPath("No path exists (energy)")

    @staticmethod
    def distance_cost(graph, path):
        total = 0.0
        for u, v in zip(path, path[1:]):
            total += float(graph[u][v].get('distance', 0))
        return total

    @staticmethod
    def energy_cost(graph, path):
        total = 0.0
        for u, v in zip(path, path[1:]):
            total += float(graph[u][v].get('energy_cost', 0))
        return total

    @staticmethod
    def apply_battery_drain(graph, path, packet_size=1):
        """
        Reduce battery level of nodes used in the path.
        Simple drain rule (tunable): each node in path loses drain_amount energy.
        """
        # Example drain rule: proportional to packet_size but bounded and integer
        drain_amount = max(1, int(round(2 * packet_size)))  # e.g., small=2, med=10, large=20
        for node in path:
            if 'energy' in graph.nodes[node]:
                current = graph.nodes[node]['energy']
                graph.nodes[node]['energy'] = max(0, current - drain_amount)
