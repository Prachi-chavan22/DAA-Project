import networkx as nx
import random

class IoTNetwork:
    def __init__(self, num_nodes=10):
        self.num_nodes = num_nodes
        self.graph = nx.Graph()
        self.generate_nodes()
        self.generate_edges()

    def generate_nodes(self):
        for i in range(self.num_nodes):
            self.graph.add_node(i, energy=random.randint(80, 100))

    def generate_edges(self):
        # Random geometric-like connections
        for i in range(self.num_nodes):
            for j in range(i+1, self.num_nodes):
                if random.random() < 0.3:  # 30% chance of connection
                    distance = random.randint(1, 20)
                    self.graph.add_edge(i, j, distance=distance)

    def assign_energy_costs(self, energy_model_fn):
        for u, v, data in self.graph.edges(data=True):
            distance = data['distance']
            data['energy_cost'] = energy_model_fn(distance)

    def get_graph(self):
        return self.graph
