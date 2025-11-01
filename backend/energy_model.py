import random

def basic_energy_model(distance):
    energy_factor = 0.8
    interference = random.uniform(1, 5)  # random noise in energy
    return distance * energy_factor + interference
