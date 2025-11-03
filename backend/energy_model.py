def advanced_energy_model(distance, packet_size=1):
    """
    Realistic-ish IoT radio transmission energy model supporting packet size.
    E_tx = E_elec * packet_size + E_amp * packet_size * distance^2

    - distance: numeric (units arbitrary)
    - packet_size: relative packet size multiplier (1 = small, 5 = med, 10 = large)
    """
    # coefficients (tunable)
    E_elec = 0.5   # electronics energy per packet unit
    E_amp = 0.02   # amplifier cost coefficient

    return (E_elec * packet_size) + (E_amp * packet_size * (distance ** 2))
