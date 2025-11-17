import json
import time
import random
import paho.mqtt.publish as publish
from datetime import datetime
import threading

# --- Variables de estado para datos con tendencia natural ---
trend_values = {}
last_update_times = {}

# --- Funciones de Ayuda ---
def generate_noise(nominal, percent, decimals=2):
    noise = random.uniform(-percent, percent)
    return round(nominal * (1 + noise / 100), decimals)

def generate_trend_value(key, nominal, min_val, max_val, step_range=1.0, oscillation_chance=0.3):
    """
    Genera un valor que cambia gradualmente con tendencia natural.
    
    Args:
        key: Identificador único para el valor (ej: 'temperature_t3')
        nominal: Valor nominal alrededor del cual oscilar
        min_val: Valor mínimo permitido
        max_val: Valor máximo permitido
        step_range: Rango máximo de cambio por iteración
        oscillation_chance: Probabilidad de cambiar la dirección de la tendencia
    """
    global trend_values, last_update_times
    
    current_time = time.time()
    
    # Si es la primera vez o hay una gran diferencia de tiempo, usar valor nominal
    if key not in trend_values or (current_time - last_update_times.get(key, 0)) > 60:
        trend_values[key] = nominal
        last_update_times[key] = current_time
        return round(trend_values[key], 2)
    
    # Determinar si cambiar la dirección de la tendencia
    if random.random() < oscillation_chance:
        # Cambiar la dirección aleatoriamente
        step = random.uniform(-step_range, step_range)
    else:
        # Continuar en la misma dirección con una ligera variación
        current_direction = 1 if trend_values[key] < nominal else -1
        step = random.uniform(0, step_range) * current_direction
    
    # Calcular nuevo valor
    new_value = trend_values[key] + step
    
    # Asegurarse de mantenerse dentro de los límites
    new_value = max(min_val, min(max_val, new_value))
    
    # Actualizar el valor
    trend_values[key] = new_value
    last_update_times[key] = current_time
    
    return round(new_value, 2)

def check_event_active(active_events, target, event_type):
    """Check if a specific event is active for a specific target"""
    return active_events.get(target, {}).get(event_type) == True

# --- Clases de Componentes de Simulación ---

class Transformer:
    def __init__(self, name):
        self.name = name
        # Initialize pump states based on transformer name (3 pumps total)
        if name == "T3":
            # T3: 2 bombas activas (1), 1 en spear (0)
            self.pump1_state = 1  # Active
            self.pump2_state = 1  # Active
            self.pump3_state = 0  # SPEAR (backup)
        elif name == "T4":
            # T4: 1 bomba activa (1), 2 en spear (0)
            self.pump1_state = 1  # Active
            self.pump2_state = 0  # SPEAR (backup)
            self.pump3_state = 0  # SPEAR (backup)
        # Initialize silicon level
        self.silicon_level = generate_trend_value(f"{name}_silicon_level", 95.0, 80.0, 100.0, 0.5, 0.4)  # Nominal level around 95%

    def update_data(self, active_events):
        # --- Fallas Físicas y Eléctricas ---
        is_overload = check_event_active(active_events, self.name, "overload")
        is_cooling_fault = check_event_active(active_events, self.name, "cooling_fault")
        is_oil_pressure_high = check_event_active(active_events, self.name, "oil_pressure_high")
        is_oil_pressure_low = check_event_active(active_events, self.name, "oil_pressure_low")
        is_transformer_temp_high = check_event_active(active_events, self.name, "transformer_temp_high")
        is_oil_temp_alert = check_event_active(active_events, self.name, "oil_temp_alert")
        is_oil_temp_fault = check_event_active(active_events, self.name, "oil_temp_fault")
        is_winding_temp_alert = check_event_active(active_events, self.name, "winding_temp_alert")
        is_winding_temp_fault = check_event_active(active_events, self.name, "winding_temp_fault")
        # Pump failures
        is_pump1_fault = check_event_active(active_events, self.name, "pump1_fault")
        is_pump2_fault = check_event_active(active_events, self.name, "pump2_fault")
        is_pump1_manual_stop = check_event_active(active_events, self.name, "pump1_manual_stop")
        is_pump2_manual_stop = check_event_active(active_events, self.name, "pump2_manual_stop")
        is_pump3_manual_stop = check_event_active(active_events, self.name, "pump3_manual_stop")

        # --- Fallas de Gases Disueltos (DGA) ---
        is_h2_high = check_event_active(active_events, self.name, "h2_high")
        is_ch4_high = check_event_active(active_events, self.name, "ch4_high")
        is_c2h6_high = check_event_active(active_events, self.name, "c2h6_high")
        is_c2h2_high = check_event_active(active_events, self.name, "c2h2_high")
        is_h2_low = check_event_active(active_events, self.name, "h2_low")
        
        # --- Fallas de Humedad en Aceite (Water in Oil) ---
        is_water_in_oil_alert = check_event_active(active_events, self.name, "water_in_oil_alert")
        is_water_in_oil_fault = check_event_active(active_events, self.name, "water_in_oil_fault")

        # --- Fallas de Línea de Agua ---
        is_water_pressure_in_high = check_event_active(active_events, self.name, "pressure_in_high")
        is_water_pressure_in_low = check_event_active(active_events, self.name, "pressure_in_low")
        is_water_pressure_out_high = check_event_active(active_events, self.name, "pressure_out_high")
        is_water_pressure_out_low = check_event_active(active_events, self.name, "pressure_out_low")
        is_water_flow_in_high = check_event_active(active_events, self.name, "flow_in_high")
        is_water_flow_in_low = check_event_active(active_events, self.name, "flow_in_low")
        is_water_flow_out_high = check_event_active(active_events, self.name, "flow_out_high")
        is_water_flow_out_low = check_event_active(active_events, self.name, "flow_out_low")
        is_water_pressure_max_20_out = check_event_active(active_events, self.name, "pressure_max_20_out")  # 20psi máx. de salida
        is_flood = check_event_active(active_events, self.name, "flood")
        is_humidity_low = check_event_active(active_events, self.name, "humidity_low")
        is_humidity_high = check_event_active(active_events, self.name, "humidity_high")

        # --- Verificación de Fallas y Definición de Estado ---
        has_fault = any([
            is_overload, is_cooling_fault, is_oil_pressure_high, is_oil_pressure_low,
            is_transformer_temp_high, is_oil_temp_fault, is_winding_temp_fault,
            is_h2_high, is_ch4_high, is_c2h6_high, is_c2h2_high, is_h2_low,
            is_water_in_oil_fault,
            is_pump1_fault, is_pump2_fault,
            is_water_pressure_in_high, is_water_pressure_in_low, is_water_pressure_out_high, is_water_pressure_out_low,
            is_water_flow_in_high, is_water_flow_in_low, is_water_flow_out_high, is_water_flow_out_low,
            is_water_pressure_max_20_out, is_flood,
            is_humidity_low, is_humidity_high
        ])

        has_manual_stop = any([is_pump1_manual_stop, is_pump2_manual_stop, is_pump3_manual_stop])

        status = 0
        if has_fault:
            status = 1
        elif has_manual_stop:
            status = 2

        # --- Simulación de Variables Físicas ---
        # Carga del transformador (normalmente entre 70-85% en operación normal)
        load_pct = generate_trend_value(f"{self.name}_load_pct", 78.0, 60.0, 90.0, 1.0, 0.3)
        if is_overload:
            load_pct = generate_trend_value(f"{self.name}_load_pct_overload", 110.0, 100.0, 120.0, 1.0, 0.1)  # Valor más constante durante sobrecarga

        # Flujo de refrigeración (nominal 40 L/s)
        cooling_flow = generate_trend_value(f"{self.name}_cooling_flow", 40.0, 35.0, 45.0, 0.5, 0.3)
        if is_cooling_fault:
            cooling_flow = generate_trend_value(f"{self.name}_cooling_flow_fault", 20.0, 15.0, 25.0, 0.5, 0.2)  # Valor más bajo en falla de refrigeración

        # Presión de aceite (nominal alrededor de 21.75 psi)
        oil_pressure = generate_trend_value(f"{self.name}_oil_pressure", 21.75, 20.0, 25.0, 0.3, 0.3)
        if is_oil_pressure_high:
            oil_pressure = generate_trend_value(f"{self.name}_oil_pressure_high", 36.0, 34.0, 38.0, 0.3, 0.1)  # Valor constante en alta presión
        elif is_oil_pressure_low:
            oil_pressure = generate_trend_value(f"{self.name}_oil_pressure_low", 7.2, 6.5, 8.0, 0.2, 0.1)  # Valor constante en baja presión

        # Temperatura de aceite (nominal alrededor de 65°C)
        oil_temperature = generate_trend_value(f"{self.name}_oil_temp", 65.0, 55.0, 75.0, 0.5, 0.3)
        if is_cooling_fault:
            oil_temperature = generate_trend_value(f"{self.name}_oil_temp_cooling_fault", oil_temperature + 20, 75.0, 90.0, 0.5, 0.2)  # Temperatura más alta en falla de refrigeración
        if is_oil_temp_alert:
            oil_temperature = generate_trend_value(f"{self.name}_oil_temp_alert", 80.0, 75.0, 85.0, 0.4, 0.2)  # Rango de alerta
        if is_oil_temp_fault:
            oil_temperature = generate_trend_value(f"{self.name}_oil_temp_fault", 95.0, 90.0, 100.0, 0.4, 0.1)  # Rango de falla

        # Temperatura de devanado (nominal alrededor de 75°C)
        winding_temp = generate_trend_value(f"{self.name}_winding_temp", 75.0, 65.0, 85.0, 0.5, 0.3)
        if is_cooling_fault:
            winding_temp = generate_trend_value(f"{self.name}_winding_temp_cooling_fault", winding_temp + 25, 85.0, 105.0, 0.5, 0.2)  # Temperatura más alta en falla de refrigeración
        if is_winding_temp_alert:
            winding_temp = generate_trend_value(f"{self.name}_winding_temp_alert", 87.5, 85.0, 95.0, 0.4, 0.2)  # Rango de alerta
        if is_winding_temp_fault:
            winding_temp = generate_trend_value(f"{self.name}_winding_temp_fault", 100.0, 95.0, 110.0, 0.4, 0.1)  # Rango de falla

        # Temperatura del transformador (relacionada con carga)
        transformer_temp = generate_trend_value(f"{self.name}_transformer_temp", 65.0 + (load_pct / 100) * 22, 60.0, 85.0, 0.5, 0.3)
        if is_transformer_temp_high:
            transformer_temp = generate_trend_value(f"{self.name}_transformer_temp_high", 85.0 + (load_pct / 100) * 22, 85.0, 110.0, 0.5, 0.2)

        # Humedad ambiente (nominal alrededor de 55%)
        ambient_humidity = generate_trend_value(f"{self.name}_ambient_humidity", 55.0, 40.0, 70.0, 1.0, 0.25)
        if is_humidity_low:
            ambient_humidity = generate_trend_value(f"{self.name}_ambient_humidity_low", 30.0, 20.0, 40.0, 1.0, 0.2)  # Humedad baja
        elif is_humidity_high:
            ambient_humidity = generate_trend_value(f"{self.name}_ambient_humidity_high", 80.0, 70.0, 90.0, 1.0, 0.2)  # Humedad alta

        # --- Simulación de Variables de Línea de Agua ---
        # New in/out pressure and flow variables (similar to existing but with new fault scenarios)
        # Under normal conditions, in/out values should be nearly equal
        # Normal operation: pressures should be the same (respecting the 20psi max output limit)
        base_pressure = generate_trend_value(f"{self.name}_water_pressure", 18.0, 15.0, 20.0, 0.3, 0.3)  # Base pressure (kept under 20psi as per requirement)
        water_pressure_in = base_pressure
        water_pressure_out = base_pressure
        
        # Handle specific input/output pressure faults
        if is_water_pressure_in_high:
            water_pressure_in = generate_trend_value(f"{self.name}_water_pressure_in_high", 25.0, 23.0, 27.0, 0.3, 0.1)  # High input pressure
        elif is_water_pressure_in_low:
            water_pressure_in = generate_trend_value(f"{self.name}_water_pressure_in_low", 8.0, 6.0, 10.0, 0.2, 0.1)   # Low input pressure
        if is_water_pressure_out_high:
            water_pressure_out = generate_trend_value(f"{self.name}_water_pressure_out_high", 25.0, 23.0, 27.0, 0.3, 0.1)  # High output pressure
        elif is_water_pressure_out_low:
            water_pressure_out = generate_trend_value(f"{self.name}_water_pressure_out_low", 8.0, 6.0, 10.0, 0.2, 0.1)   # Low output pressure
        
        # For the "max 20 psi of output" fault scenario: when this fault is active, the output pressure exceeds the normal max
        if is_water_pressure_max_20_out:
            water_pressure_out = generate_trend_value(f"{self.name}_water_pressure_max_20_out", 30.0, 25.0, 35.0, 0.5, 0.1)  # Pressure exceeding the max limit (fault condition: >20psi)
            # When output pressure fault occurs, input pressure may also be affected but can be different
            water_pressure_in = generate_trend_value(f"{self.name}_water_pressure_in_fault", 25.0, 20.0, 30.0, 0.5, 0.2)   # Adjusted input pressure

        # Under normal conditions, flow in should equal flow out
        base_flow = generate_trend_value(f"{self.name}_water_flow", 15.0, 12.0, 18.0, 0.5, 0.3)  # Base flow rate
        water_flow_in = base_flow
        water_flow_out = base_flow
        
        # Handle specific input/output flow faults
        if is_water_flow_in_high:
            water_flow_in = generate_trend_value(f"{self.name}_water_flow_in_high", 23.0, 20.0, 26.0, 0.5, 0.1)  # High input flow
        elif is_water_flow_in_low:
            water_flow_in = generate_trend_value(f"{self.name}_water_flow_in_low", 5.0, 3.0, 7.0, 0.3, 0.1)   # Low input flow
        if is_water_flow_out_high:
            water_flow_out = generate_trend_value(f"{self.name}_water_flow_out_high", 23.0, 20.0, 26.0, 0.5, 0.1)  # High output flow
        elif is_water_flow_out_low:
            water_flow_out = generate_trend_value(f"{self.name}_water_flow_out_low", 5.0, 3.0, 7.0, 0.3, 0.1)   # Low output flow

        # Existing pressure and flow variables (based on output values but responsive to in/out faults)
        water_pressure = water_pressure_out  # Using output pressure value for main variable
        water_flow = water_flow_out  # Using output flow value for main variable
        
        flood_sensor_status = 1 if is_flood else 0

        # --- Pump and SPEAR Logic ---
        # Reset states based on faults or manual stop
        if self.name == "T3":
            # For T3: 2 active pumps (pump1, pump2) and 1 spear (pump3) initially
            if is_pump1_manual_stop:
                self.pump1_state = 2
            elif is_pump1_fault:
                self.pump1_state = 0
            else:
                self.pump1_state = 1
                
            if is_pump2_manual_stop:
                self.pump2_state = 2
            elif is_pump2_fault:
                self.pump2_state = 0
            else:
                self.pump2_state = 1
                
            if is_pump3_manual_stop:
                self.pump3_state = 2
            # If any active pump fails, activate the spear pump
            elif (self.pump1_state == 0 or self.pump2_state == 0) and self.pump3_state == 0:
                self.pump3_state = 1  # Activate spear pump if any active pump fails
            elif self.pump1_state == 1 and self.pump2_state == 1:
                self.pump3_state = 0  # Keep spear pump as backup if both active pumps are running
        elif self.name == "T4":
            # For T4: 1 active pump (pump1) and 2 spear pumps (pump2, pump3) initially
            if is_pump1_manual_stop:
                self.pump1_state = 2
            elif is_pump1_fault:
                self.pump1_state = 0
            else:
                self.pump1_state = 1
                
            if is_pump2_manual_stop:
                self.pump2_state = 2
            if is_pump3_manual_stop:
                self.pump3_state = 2
            # If active pump fails, activate the spear pumps
            elif self.pump1_state == 0:
                self.pump2_state = 1  # Activate spear pump2
                self.pump3_state = 1  # Activate spear pump3
            else:
                # If active pump is running, spear pumps stay as backup
                self.pump2_state = 0  # Keep pump2 as backup
                self.pump3_state = 0  # Keep pump3 as backup

        # Update silicon level with some degradation over time
        if self.silicon_level > 80:  # Only degrade if above minimum threshold
            self.silicon_level = generate_trend_value(f"{self.name}_silicon_level", self.silicon_level - 0.2, 80.0, 95.0, 0.3, 0.4)
        else:
            # Maintain minimum level if it gets too low
            self.silicon_level = generate_trend_value(f"{self.name}_silicon_level", 85.0, 80.0, 95.0, 0.5, 0.4)

        # --- Simulación de Variables de Gases (DGA) ---
        # Concentraciones normales de gases en aceite aislante
        h2_concentration_ppm = generate_trend_value(f"{self.name}_h2_concentration", 500.0, 400.0, 600.0, 8.0, 0.25)
        ch4_concentration_ppm = generate_trend_value(f"{self.name}_ch4_concentration", 200.0, 150.0, 250.0, 6.0, 0.25)
        c2h6_concentration_ppm = generate_trend_value(f"{self.name}_c2h6_concentration", 100.0, 70.0, 130.0, 4.0, 0.25)
        c2h2_concentration_ppm = generate_trend_value(f"{self.name}_c2h2_concentration", 50.0, 30.0, 70.0, 2.5, 0.2)  # Acetileno normalmente bajo

        if is_h2_high:
            h2_concentration_ppm = generate_trend_value(f"{self.name}_h2_high", 1500.0, 1400.0, 1600.0, 10.0, 0.1)  # Valor constante en alta concentración
        if is_ch4_high:
            ch4_concentration_ppm = generate_trend_value(f"{self.name}_ch4_high", 800.0, 700.0, 900.0, 10.0, 0.1)
        if is_c2h6_high:
            c2h6_concentration_ppm = generate_trend_value(f"{self.name}_c2h6_high", 500.0, 400.0, 600.0, 10.0, 0.1)
        if is_c2h2_high:
            c2h2_concentration_ppm = generate_trend_value(f"{self.name}_c2h2_high", 500.0, 400.0, 600.0, 10.0, 0.1)
        if is_h2_low:
            h2_concentration_ppm = generate_trend_value(f"{self.name}_h2_low", 11.0, 10.0, 15.0, 1.0, 0.1) # Valor bajo constante

        # --- Simulación de Variables de Humedad en Aceite (Water in Oil) ---
        water_in_oil_ppm = generate_trend_value(f"{self.name}_water_in_oil", 5.5, 4.0, 7.0, 0.15, 0.3)  # Rango nominal más preciso: 4-7 ppm
        
        if is_water_in_oil_alert:
            water_in_oil_ppm = generate_trend_value(f"{self.name}_water_in_oil_alert", 9.0, 7.0, 11.0, 0.2, 0.2)  # Rango de alerta: 7-11 ppm
        elif is_water_in_oil_fault:
            water_in_oil_ppm = generate_trend_value(f"{self.name}_water_in_oil_fault", 13.0, 11.0, 15.0, 0.2, 0.1)  # Rango de falla: 11-15 ppm

        # --- Consolidación de Datos ---
        payload = {
            # Specific status variables
            f"{self.name.lower()}_status": status,  # T3_status or T4_status
            # Estado
            "status": status,
            # Físicas
            f"{self.name}_cooling_flow_lps": cooling_flow,
            f"{self.name}_oil_temperature": round(oil_temperature, 2),
            f"{self.name}_winding_temp": round(winding_temp, 2),
            f"{self.name}_transformer_temp": transformer_temp,
            f"{self.name}_hot_spot_temp": round(winding_temp + 10, 2),
            f"{self.name}_ambient_temp": generate_trend_value(f"{self.name}_ambient_temp", 25.0, 20.0, 30.0, 0.3, 0.25),
            f"{self.name}_ambient_humidity": ambient_humidity,
            f"{self.name}_oil_pressure": round(oil_pressure, 2),
            f"{self.name}_fan_status": 1 if oil_temperature > 75 else 0,
            f"{self.name}_pump_status": 1 if cooling_flow > 10 else 0,
            f"{self.name}_tap_changer_position": random.randint(1, 9),
            f"{self.name}_transformer_load_pct": load_pct,
            # Pump states (3 pumps per transformer)
            f"{self.name}_pump1_status": self.pump1_state,
            f"{self.name}_pump2_status": self.pump2_state,
            f"{self.name}_pump3_status": self.pump3_state,
            # Silicon level
            f"{self.name}_silicon_level_pct": round(self.silicon_level, 2),
            # DGA
            f"{self.name}_hidrogeno_concentration_ppm": h2_concentration_ppm,
            f"{self.name}_metano_concentration_ppm": ch4_concentration_ppm,
            f"{self.name}_etano_concentration_ppm": c2h6_concentration_ppm,
            f"{self.name}_acetileno_concentration_ppm": c2h2_concentration_ppm,
            f"{self.name}_water_in_oil_ppm": water_in_oil_ppm,
            # Water Line
            f"{self.name}_water_pressure_psi": round(water_pressure, 2),
            f"{self.name}_water_pressure_in_psi": round(water_pressure_in, 2),
            f"{self.name}_water_pressure_out_psi": round(water_pressure_out, 2),
            f"{self.name}_flowmeter_lps": round(water_flow, 2),
            f"{self.name}_flowmeter_in_lps": round(water_flow_in, 2),
            f"{self.name}_flowmeter_out_lps": round(water_flow_out, 2),
            f"{self.name}_flood_sensor_status": flood_sensor_status,
        }
        return payload

class BatteryCharger:
    def __init__(self):
        pass

    def update_data(self, active_events):
        is_fault = check_event_active(active_events, "BATTERY", "fault")
        is_temp_high = check_event_active(active_events, "BATTERY", "temp_high")
        is_output_voltage_low = check_event_active(active_events, "BATTERY", "output_voltage_low")
        is_current_high = check_event_active(active_events, "BATTERY", "current_high")
        is_input_voltage_low = check_event_active(active_events, "BATTERY", "input_voltage_low")

        # --- Verificación de Fallas y Definición de Estado ---
        has_fault = any([
            is_fault, is_temp_high, is_output_voltage_low, is_current_high, is_input_voltage_low
        ])
        status = 1 if has_fault else 0
        
        charger_status = 0
        if is_fault:
            charger_status = 1

        battery_current = generate_trend_value("battery_current", 5.0, 4.0, 6.0, 0.1, 0.3)
        if is_current_high:
            battery_current = generate_trend_value("battery_current_high", 20.0, 18.0, 22.0, 0.5, 0.1) # Valor constante en alta corriente

        battery_temp = generate_trend_value("battery_temp", 30.0, 25.0, 35.0, 0.2, 0.3)
        if is_temp_high:
            battery_temp = generate_trend_value("battery_temp_high", 40.0, 38.0, 42.0, 0.3, 0.1) # Valor constante en alta temperatura

        battery_input_voltage = generate_trend_value("battery_input_voltage", 220.0, 215.0, 225.0, 0.5, 0.1)
        if is_input_voltage_low:
            battery_input_voltage = generate_trend_value("battery_input_voltage_low", 190.0, 185.0, 195.0, 0.5, 0.1) # Valor constante en baja tensión

        battery_output_voltage = generate_trend_value("battery_output_voltage", 125.0, 120.0, 130.0, 0.3, 0.1)
        if is_output_voltage_low:
            battery_output_voltage = generate_trend_value("battery_output_voltage_low", 110.0, 105.0, 115.0, 0.3, 0.1) # Valor constante en baja tensión

        return {
            "general_status": status,  # General status variable for battery charger
            "status": status,
            "battery_current_A": battery_current,
            "battery_input_voltage_V": battery_input_voltage,  # New battery input voltage
            "battery_output_voltage_V": battery_output_voltage,  # New battery output voltage
            "battery_state_of_charge_pct": generate_trend_value("battery_state_of_charge", 98.0, 80.0, 100.0, 0.2, 0.2),
            "battery_temp_C": round(battery_temp, 2),
            "charger_status": charger_status,
        }

class Substation:
    def update_data(self, active_events):
        # Nuevas fallas del resumen
        is_temp_high = check_event_active(active_events, "SUBSTATION", "temp_high")
        is_temp_low = check_event_active(active_events, "SUBSTATION", "temp_low")
        is_freq_high = check_event_active(active_events, "SUBSTATION", "frequency_high")
        is_freq_low = check_event_active(active_events, "SUBSTATION", "frequency_low")

        # --- Verificación de Fallas y Definición de Estado ---
        has_fault = any([
            is_temp_high, is_temp_low, is_freq_high, is_freq_low
        ])
        status = 1 if has_fault else 0

        room_temp = generate_trend_value("room_temp_control", 22.0, 20.0, 25.0, 0.2, 0.25)
        if is_temp_high:
            room_temp = generate_trend_value("room_temp_high", 30.0, 29.0, 31.0, 0.2, 0.1) # Valor constante en alta temperatura
        elif is_temp_low:
            room_temp = generate_trend_value("room_temp_low", 10.0, 9.5, 10.5, 0.2, 0.1) # Valor constante en baja temperatura
            
        grid_freq = generate_trend_value("grid_frequency", 50.0, 49.9, 50.1, 0.02, 0.2)
        if is_freq_high:
            grid_freq = generate_trend_value("grid_freq_high", 51.0, 50.9, 51.0, 0.02, 0.1) # Valor constante en alta frecuencia
        elif is_freq_low:
            grid_freq = generate_trend_value("grid_freq_low", 49.0, 49.0, 49.1, 0.02, 0.1) # Valor constante en baja frecuencia

        return {
            "general_status": status,  # General status variable for substation
            "status": status,
            "room_temp_control": round(room_temp, 2),
            "grid_frequency_Hz": round(grid_freq, 2),
            "room_humidity": generate_trend_value("room_humidity", 50.0, 45.0, 55.0, 0.5, 0.25), # Rango nominal más preciso 45-55%
        }

# --- Bucle Principal de Simulación ---
def simulation_loop(stop_event, active_event_ref, interval_seconds, immediate_refresh_event=None):
    print("Bucle de simulación iniciado.")

    t3 = Transformer("T3")
    t4 = Transformer("T4")
    charger = BatteryCharger()
    station = Substation()

    # Configuraciones de los dispositivos MQTT
    mqtt_devices = [
        {
            "name": "T3",
            "token": "",
            "data_func": t3.update_data
        },
        {
            "name": "T4",
            "token": "",
            "data_func": t4.update_data
        },
        {
            "name": "Baterías",
            "token": "",
            "data_func": charger.update_data
        },
        {
            "name": "General",
            "token": "",
            "data_func": station.update_data
        }
    ]

    while not stop_event.is_set():
        # Send data normally at the beginning of the cycle or when immediate refresh is triggered
        try:
            for device in mqtt_devices:
                payload = device["data_func"](active_event_ref)
                
                # Extraer el estado y publicarlo como atributo
                status_payload = {"status": payload.pop("status", 0)} # Extraer con valor por defecto
                publish.single(
                    topic="",
                    payload=json.dumps(status_payload),
                    hostname="",
                    port=,
                    auth={'username': device["token"], 'password': ''}
                )

                # Añadir timestamp y enviar telemetría
                payload["ts"] = int(time.time() * 1000)
                
                publish.single(
                    topic="v1/devices/me/telemetry",
                    payload=json.dumps(payload),
                    hostname="iot.sstech.cl",
                    port=11883,
                    auth={'username': device["token"], 'password': ''}
                )
                print(f"Datos de '{device['name']}' enviados a Thingsboard a las {datetime.now().isoformat()}")

        except Exception as e:
            print(f"Error en el bucle de simulación: {e}")

        # Wait for the interval but allow immediate refresh by checking the event periodically
        remaining_time = interval_seconds
        while remaining_time > 0 and not stop_event.is_set():
            # Check if there's an immediate refresh request
            if immediate_refresh_event and immediate_refresh_event.is_set():
                immediate_refresh_event.clear()  # Clear the event
                print("Immediate refresh requested, sending data now...")
                break  # Break the wait to send data immediately

            # Wait for 1 second or until the immediate refresh event is set
            if immediate_refresh_event:
                immediate_refresh_event.wait(timeout=1)
            else:
                time.sleep(1)
            
            remaining_time -= 1

    print("Bucle de simulación detenido.")
