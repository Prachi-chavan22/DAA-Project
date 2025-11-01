import networkx as nx

class RoutingEngine:

    @staticmethod
    def shortest_path_distance(graph, source, target):
        """
        Normal routing using only distance.
        """
        return nx.shortest_path(graph, source=source, target=target, weight='distance')

    @staticmethod
    def shortest_path_energy(graph, source, target):
        """
        Energy-efficient routing using energy_cost.
        """
        return nx.shortest_path(graph, source=source, target=target, weight='energy_cost')

    @staticmethod
    def distance_cost(graph, path):
        total = 0
        for u, v in zip(path, path[1:]):
            total += graph[u][v]['distance']
        return total

    @staticmethod
    def energy_cost(graph, path):
        total = 0
        for u, v in zip(path, path[1:]):
            total += graph[u][v]['energy_cost']
        return total
