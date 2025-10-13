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
    return active_events.get(target, {}).get(event_type) == True

# --- Clases de Componentes de Simulación ---

class Transformer:
    def __init__(self, name):
        self.name = name

    def update_data(self, active_events):
        # Fallas existentes
        is_overload = check_event_active(active_events, self.name, "overload")
        is_cooling_fault = check_event_active(active_events, self.name, "cooling_fault")
        is_c2h2_spike = check_event_active(active_events, self.name, "c2h2_spike")
        
        # Nuevas fallas del resumen
        is_oil_pressure_high = check_event_active(active_events, self.name, "oil_pressure_high")
        is_oil_pressure_low = check_event_active(active_events, self.name, "oil_pressure_low")
        is_h2_high = check_event_active(active_events, self.name, "h2_high")

        # Simulación de variables
        load_pct = generate_noise(78, 10)
        if is_overload:
            load_pct = generate_noise(110, 5)

        cooling_flow = generate_noise(40, 3)
        if is_cooling_fault:
            cooling_flow = generate_noise(8, 40)

        c2h2_ppm = generate_noise(0.5, 15)
        if is_c2h2_spike:
            c2h2_ppm = generate_noise(15, 25)
        
        oil_pressure = generate_noise(1.5, 5)
        if is_oil_pressure_high:
            oil_pressure = random.uniform(2.37, 2.62)
        elif is_oil_pressure_low:
            oil_pressure = random.uniform(0.47, 0.52)

        h2_ppm = generate_noise(12, 10)
        if is_h2_high:
            h2_ppm = random.uniform(18, 22)

        top_oil_temp = generate_noise(60 + (load_pct / 100) * 20, 4)
        winding_temp = generate_noise(70 + (load_pct / 100) * 25, 4)

        return {
            f"{self.name}_cooling_flow_lps": cooling_flow,
            f"{self.name}_top_oil_temp": top_oil_temp,
            f"{self.name}_winding_temp": winding_temp,
            f"{self.name}_hot_spot_temp": winding_temp + 10,
            f"{self.name}_ambient_temp": generate_noise(25, 10),
            f"{self.name}_ambient_humidity": generate_noise(50, 15),
            f"{self.name}_oil_pressure": round(oil_pressure, 2),
            f"{self.name}_H2_ppm": round(h2_ppm, 2),
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
        is_temp_high = check_event_active(active_events, "BATTERY", "temp_high")
        
        charger_status = "FLOAT"
        battery_voltage = generate_noise(125, 2)
        battery_current = generate_noise(5, 10)
        battery_temp = generate_noise(30, 5)

        if is_fault:
            charger_status = "FAULT"
            battery_voltage = generate_noise(110, 5)
            battery_current = generate_noise(-15, 20)
        
        if is_temp_high:
            battery_temp = random.uniform(38, 42)

        return {
            "battery_voltage_V": battery_voltage,
            "battery_current_A": battery_current,
            "battery_state_of_charge_pct": generate_noise(98, 2),
            "battery_temp_C": round(battery_temp, 2),
            "charger_status": charger_status,
        }

class Substation:
    def update_data(self, active_events):
        # Fallas existentes
        is_flood = check_event_active(active_events, "SUBSTATION", "flood")
        
        # Nuevas fallas del resumen
        is_temp_high = check_event_active(active_events, "SUBSTATION", "temp_high")
        is_temp_low = check_event_active(active_events, "SUBSTATION", "temp_low")
        is_freq_high = check_event_active(active_events, "SUBSTATION", "frequency_high")
        is_freq_low = check_event_active(active_events, "SUBSTATION", "frequency_low")

        flood_status = 1 if is_flood else 0
        
        room_temp = generate_noise(22, 3)
        if is_temp_high:
            room_temp = random.uniform(29.1, 30.9)
        elif is_temp_low:
            room_temp = random.uniform(9.7, 10.3)
            
        grid_freq = generate_noise(50, 0.1)
        if is_freq_high:
            grid_freq = random.uniform(50.94, 51.05)
        elif is_freq_low:
            grid_freq = random.uniform(48.95, 49.04)

        return {
            "room_temp_control": round(room_temp, 2),
            "grid_frequency_Hz": round(grid_freq, 2),
            "flood_sensor_status": flood_status,
            "room_humidity": generate_noise(50, 10), # Rango nominal 45-55%
        }

class WaterLine:
    def __init__(self):
        pass

    def update_data(self, active_events):
        is_pressure_high = check_event_active(active_events, "WATERLINE", "pressure_high")
        is_pressure_low = check_event_active(active_events, "WATERLINE", "pressure_low")
        is_flow_high = check_event_active(active_events, "WATERLINE", "flow_high")
        is_flow_low = check_event_active(active_events, "WATERLINE", "flow_low")

        water_pressure = generate_noise(50, 5) # Nominal
        if is_pressure_high:
            water_pressure = random.uniform(66.5, 73.5)
        elif is_pressure_low:
            water_pressure = random.uniform(28.5, 31.5)

        water_flow = generate_noise(15, 10) # Nominal
        if is_flow_high:
            water_flow = random.uniform(23.75, 26.25)
        elif is_flow_low:
            water_flow = random.uniform(4.75, 5.25)
            
        return {
            "water_pressure_psi": round(water_pressure, 2),
            "flowmeter_lps": round(water_flow, 2),
        }

# --- Bucle Principal de Simulación ---
def simulation_loop(simulation_running_flag, active_event_ref, mqtt_config, interval_seconds):
    print(f"Bucle de simulación iniciado con la configuración: {mqtt_config['note']}")

    t3 = Transformer("T3")
    t4 = Transformer("T4")
    charger = BatteryCharger()
    station = Substation()
    water_line = WaterLine()

    while simulation_running_flag():
        try:
            full_payload = {
                "ts": int(time.time() * 1000),
                "device": "Subestacion_Cordillera"
            }

            full_payload.update(t3.update_data(active_event_ref))
            full_payload.update(t4.update_data(active_event_ref))
            full_payload.update(charger.update_data(active_event_ref))
            full_payload.update(station.update_data(active_event_ref))
            full_payload.update(water_line.update_data(active_event_ref))

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
        
        time.sleep(interval_seconds)

    print("Bucle de simulación detenido.")