import json
import time
import random
import paho.mqtt.publish as publish
from datetime import datetime

# --- Funciones de Ayuda ---
def generate_noise(nominal, percent, decimals=2):
    noise = random.uniform(-percent, percent)
    return round(nominal * (1 + noise / 100), decimals)

def check_event_active(active_events, target, event_type):
    """Check if a specific event is active for a specific target"""
    if target == "BATTERY":
        return active_events.get("BATTERY", {}).get(event_type) == True
    elif target == "SUBSTATION":
        return active_events.get("SUBSTATION", {}).get(event_type) == True
    else:  # T3 or T4
        return active_events.get(target, {}).get(event_type) == True

# --- Clases de Componentes de Simulación ---

class Transformer:
    def __init__(self, name):
        self.name = name

    def update_data(self, active_events):
        # Check for multiple simultaneous events
        is_overload = check_event_active(active_events, self.name, "overload")
        is_cooling_fault = check_event_active(active_events, self.name, "cooling_fault")
        is_c2h2_spike = check_event_active(active_events, self.name, "c2h2_spike")

        load_pct = generate_noise(78, 10)
        if is_overload:
            load_pct = generate_noise(110, 5)

        cooling_flow = generate_noise(40, 3)
        if is_cooling_fault:
            cooling_flow = generate_noise(8, 40)

        c2h2_ppm = generate_noise(0.5, 15)
        if is_c2h2_spike:
            c2h2_ppm = generate_noise(15, 25)

        top_oil_temp = generate_noise(60 + (load_pct / 100) * 20, 4)
        winding_temp = generate_noise(70 + (load_pct / 100) * 25, 4)

        return {
            f"{self.name}_cooling_flow_lps": cooling_flow,
            f"{self.name}_top_oil_temp": top_oil_temp,
            f"{self.name}_winding_temp": winding_temp,
            f"{self.name}_hot_spot_temp": winding_temp + 10,
            f"{self.name}_ambient_temp": generate_noise(25, 10),
            f"{self.name}_ambient_humidity": generate_noise(50, 15),
            f"{self.name}_oil_pressure": generate_noise(1.5, 5),
            f"{self.name}_H2_ppm": generate_noise(12, 10),
            f"{self.name}_C2H2_ppm": c2h2_ppm,
            f"{self.name}_fan_status": "ON" if top_oil_temp > 75 else "OFF",
            f"{self.name}_pump_status": "ON" if cooling_flow > 10 else "OFF",
            f"{self.name}_tap_changer_position": random.randint(1, 9),
            f"{self.name}_transformer_load_pct": load_pct,
        }

class BatteryCharger:
    def __init__(self):
        pass

    def update_data(self, active_events):
        is_fault = check_event_active(active_events, "BATTERY", "fault")
        
        charger_status = "FLOAT"
        battery_voltage = generate_noise(125, 2)
        battery_current = generate_noise(5, 10)

        if is_fault:
            charger_status = "FAULT"
            battery_voltage = generate_noise(110, 5)
            battery_current = generate_noise(-15, 20)

        return {
            "battery_voltage_V": battery_voltage,
            "battery_current_A": battery_current,
            "battery_state_of_charge_pct": generate_noise(98, 2),
            "battery_temp_C": generate_noise(30, 5),
            "charger_status": charger_status,
        }

class Substation:
    def update_data(self, active_events):
        is_flood = check_event_active(active_events, "SUBSTATION", "flood")
        flood_status = 1 if is_flood else 0

        return {
            "room_temp_control": generate_noise(22, 3),
            "grid_frequency_Hz": generate_noise(50, 0.1),
            "flood_sensor_status": flood_status,
        }

# --- Bucle Principal de Simulación ---
def simulation_loop(simulation_running_flag, active_event_ref, mqtt_config, interval_seconds):
    print(f"Bucle de simulación iniciado con la configuración: {mqtt_config['note']}")

    t3 = Transformer("T3")
    t4 = Transformer("T4")
    charger = BatteryCharger()
    station = Substation()

    while simulation_running_flag():
        try:
            # Create the active events structure based on the current active_event_ref
            # This allows turning events on/off without resetting the entire state
            full_payload = {
                "ts": int(time.time() * 1000),
                "device": "Subestacion_Cordillera"
            }

            full_payload.update(t3.update_data(active_event_ref))
            full_payload.update(t4.update_data(active_event_ref))
            full_payload.update(charger.update_data(active_event_ref))
            full_payload.update(station.update_data(active_event_ref))

            publish.single(
                topic=mqtt_config['topic'],
                payload=json.dumps(full_payload),
                hostname=mqtt_config['broker'],
                port=mqtt_config['port'],
                auth={'username': mqtt_config['username'], 'password': ''}
            )
            
            print(f"Datos consolidados enviados a {mqtt_config['broker']} a las {datetime.now().isoformat()}")

        except Exception as e:
            print(f"Error en el bucle de simulación: {e}")
        
        # Wait for the interval, but check for the stop signal every second
        for _ in range(interval_seconds):
            if not simulation_running_flag():
                break
            time.sleep(1)

    print("Bucle de simulación detenido.")