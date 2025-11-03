import networkx as nx
import random

class IoTNetwork:
    def __init__(self, num_nodes=10):
        self.num_nodes = num_nodes
        self.graph = nx.Graph()
        self.generate_nodes()
        self.generate_edges()

    def generate_nodes(self):
        """
        Create nodes and initialize their battery/energy level (0-100).
        """
        for i in range(self.num_nodes):
            # energy percentage (0 - dead, 100 - full)
            self.graph.add_node(i, energy=random.randint(80, 100))

    def generate_edges(self):
        """
        Random geometric-like connections with a 30% connection chance.
        Each edge has a 'distance' attribute (int).
        """
        for i in range(self.num_nodes):
            for j in range(i + 1, self.num_nodes):
                if random.random() < 0.3:  # 30% chance of connection
                    distance = random.randint(1, 20)
                    self.graph.add_edge(i, j, distance=distance)

    def assign_energy_costs(self, energy_model_fn, packet_size=1):
        """
        Compute per-edge energy_cost using provided energy model function.
        energy_model_fn(distance, packet_size) -> energy_cost (float)
        """
        for u, v, data in self.graph.edges(data=True):
            distance = data.get('distance', 1)
            data['energy_cost'] = energy_model_fn(distance, packet_size)

    def fail_random_node(self):
        """
        Mark a random alive node as failed (energy = 0). Returns node id or None if none available.
        """
        alive_nodes = [n for n, d in self.graph.nodes(data=True) if d.get('energy', 0) > 0]
        if not alive_nodes:
            return None
        node = random.choice(alive_nodes)
        self.graph.nodes[node]['energy'] = 0
        return node

    def get_graph(self):
        return self.graph
