from flask import Flask, render_template, request, jsonify
import threading
from simulation import simulation_loop

app = Flask(__name__)

# --- Estado de la Simulación ---
simulation_thread = None
simulation_stop_event = threading.Event() # Usar un Event para un control más robusto
immediate_refresh_event = threading.Event()  # Event to trigger immediate data refresh
# Dictionary to track multiple simultaneous active events
active_event = {
    "T3": {},
    "T4": {},
    "BATTERY": {},
    "SUBSTATION": {},
    "WATERLINE": {}
}

# --- Rutas de la Interfaz ---
@app.route('/')
def index():
    return render_template('index.html')

# --- Rutas de la API ---
@app.route('/start', methods=['POST'])
def start_simulation():
    global simulation_thread, simulation_stop_event, immediate_refresh_event
    
    data = request.get_json()
    interval = int(data.get('interval', 15))

    if simulation_thread is None or not simulation_thread.is_alive():
        simulation_stop_event.clear() # Limpiar el evento de detención para la nueva ejecución
        immediate_refresh_event.clear()  # Clear the immediate refresh event
        simulation_thread = threading.Thread(
            target=simulation_loop, 
            args=(simulation_stop_event, active_event, interval, immediate_refresh_event)
        )
        simulation_thread.daemon = True
        simulation_thread.start()
        return jsonify({"status": "Running", "message": "Simulación iniciada."})
    
    return jsonify({"status": "Running", "message": "La simulación ya está en ejecución."})

@app.route('/stop', methods=['POST'])
def stop_simulation():
    global simulation_thread, simulation_stop_event
    if simulation_thread and simulation_thread.is_alive():
        simulation_stop_event.set() # Enviar señal para detener el bucle
        simulation_thread.join()    # Esperar a que el hilo termine (será rápido)
        simulation_thread = None
        return jsonify({"status": "Stopped", "message": "Simulación detenida correctamente."})
    return jsonify({"status": "Stopped", "message": "La simulación no estaba en ejecución."})

@app.route('/trigger_event', methods=['POST'])
def trigger_event():
    global active_event, immediate_refresh_event
    data = request.get_json()
    event_name = data.get("event")
    
    if not event_name or event_name == "none":
        # Turn off all events - reset to normal operation
        active_event.update({
            "T3": {},
            "T4": {},
            "BATTERY": {},
            "SUBSTATION": {},
            "WATERLINE": {}
        })
        msg = "Operación normal - todos los eventos desactivados."
        print(msg)
        # Trigger immediate refresh after clearing events
        immediate_refresh_event.set()
        return jsonify({"status": "Running", "message": msg})

    try:
        target, event_type = event_name.split('_', 1)
        target = target.upper()
        
        # Toggle the specific event on/off
        if active_event[target].get(event_type) == True:
            # Turn off the event
            del active_event[target][event_type]
            msg = f"Evento '{event_type}' desactivado para el objetivo '{target}'."
        else:
            # Turn on the event
            active_event[target][event_type] = True
            msg = f"Evento '{event_type}' activado para el objetivo '{target}'."
        
        print(msg)
        # Trigger immediate refresh after changing event status
        immediate_refresh_event.set()
        return jsonify({"status": "Running", "message": msg})
    except (ValueError, KeyError) as e:
        msg = f"Formato de evento inválido o clave no encontrada: {event_name}"
        print(f"{msg} - Error: {e}")
        return jsonify({"status": "Error", "message": msg}), 400

@app.route('/api/status', methods=['GET'])
def get_status():
    global simulation_thread, active_event
    
    # El estado de la simulación se deriva directamente del estado del hilo
    simulation_running = simulation_thread is not None and simulation_thread.is_alive()
        
    return jsonify({
        "simulation_running": simulation_running,
        "active_events": active_event
    })

@app.route('/trigger_immediate_refresh', methods=['POST'])
def trigger_immediate_refresh():
    global immediate_refresh_event
    try:
        immediate_refresh_event.set()
        return jsonify({
            "status": "success",
            "message": "Immediate refresh triggered"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)