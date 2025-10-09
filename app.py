from flask import Flask, render_template, request, jsonify
import threading
import database as db
from simulation import simulation_loop

# Inicializar la base de datos al arrancar
db.init_db()

app = Flask(__name__)

# --- Estado de la Simulación ---
simulation_thread = None
simulation_running = False
# Dictionary to track multiple simultaneous active events
active_event = {
    "T3": {},
    "T4": {},
    "BATTERY": {},
    "SUBSTATION": {}
}

# --- Rutas de la Interfaz ---
@app.route('/')
def index():
    return render_template('index.html')

# --- Rutas de la API ---
@app.route('/api/mqtt_configs', methods=['GET'])
def get_configs():
    configs = db.get_all_configs()
    return jsonify(configs)

@app.route('/api/mqtt_configs', methods=['POST'])
def add_new_config():
    data = request.get_json()
    if not all(k in data for k in ['note', 'broker', 'port', 'topic']):
        return jsonify({"success": False, "error": "Faltan campos requeridos."}), 400
    
    result = db.add_config(
        data['note'],
        data['broker'],
        int(data['port']),
        data['topic'],
        data.get('username', '') # username es opcional
    )

    if result["success"]:
        return jsonify(result), 201
    else:
        return jsonify(result), 409 # 409 Conflict por nota duplicada

@app.route('/api/mqtt_configs/<int:config_id>', methods=['DELETE'])
def delete_config_route(config_id):
    result = db.delete_config(config_id)
    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 404 # 404 Not Found si el ID no existe

@app.route('/start', methods=['POST'])
def start_simulation():
    global simulation_thread, simulation_running
    
    data = request.get_json()
    config_id = data.get('config_id')
    interval = int(data.get('interval', 15))

    if not config_id:
        return jsonify({"status": "Error", "message": "No se proporcionó un ID de configuración."}), 400

    mqtt_config = db.get_config_by_id(config_id)
    if not mqtt_config:
        return jsonify({"status": "Error", "message": f"No se encontró una configuración con ID {config_id}."}), 404

    if simulation_thread is None or not simulation_thread.is_alive():
        simulation_running = True
        simulation_thread = threading.Thread(
            target=simulation_loop, 
            args=(lambda: simulation_running, active_event, mqtt_config, interval)
        )
        simulation_thread.daemon = True
        simulation_thread.start()
        return jsonify({"status": "Running", "message": f"Simulación iniciada con la configuración '{mqtt_config['note']}'."})
    
    return jsonify({"status": "Running", "message": "La simulación ya está en ejecución."})

@app.route('/stop', methods=['POST'])
def stop_simulation():
    global simulation_thread, simulation_running
    if simulation_thread and simulation_thread.is_alive():
        simulation_running = False
        simulation_thread.join()
        simulation_thread = None
        return jsonify({"status": "Stopped", "message": "Simulación detenida correctamente."})
    return jsonify({"status": "Stopped", "message": "La simulación no estaba en ejecución."})

@app.route('/trigger_event', methods=['POST'])
def trigger_event():
    global active_event
    data = request.get_json()
    event_name = data.get("event")
    
    if not event_name or event_name == "none":
        # Turn off all events - reset to normal operation
        active_event.update({
            "T3": {},
            "T4": {},
            "BATTERY": {},
            "SUBSTATION": {}
        })
        msg = "Operación normal - todos los eventos desactivados."
        print(msg)
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
        return jsonify({"status": "Running", "message": msg})
    except ValueError:
        msg = f"Formato de evento inválido: {event_name}"
        print(msg)
        return jsonify({"status": "Error", "message": msg}), 400

@app.route('/api/status', methods=['GET'])
def get_status():
    global simulation_running, active_event, simulation_thread
    # Asegurarse de que el estado es consistente
    if simulation_thread is None or not simulation_thread.is_alive():
        simulation_running = False
        
    return jsonify({
        "simulation_running": simulation_running,
        "active_events": active_event
    })

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
