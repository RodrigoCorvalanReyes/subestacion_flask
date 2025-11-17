document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-sim');
    const stopBtn = document.getElementById('stop-sim');
    const statusIndicator = document.getElementById('sim-status-indicator');
    const statusText = document.getElementById('sim-status-text');
    const logOutput = document.getElementById('log-output');
    const intervalInput = document.getElementById('interval-seconds');
    const deviceStatusList = document.getElementById('device-status-list');
    const eventTabsContent = document.getElementById('eventTabsContent');

    const translationMap = {
        // T3 and T4 Faults
        'overload': 'Sobrecarga',
        'cooling_fault': 'Falla Refrigeración',
        'transformer_temp_high': 'Temp. Transformador Alta',
        'oil_temp_alert': 'Alerta Temp. Aceite',
        'oil_temp_fault': 'Falla Temp. Aceite',
        'winding_temp_alert': 'Alerta Temp. Devanado',
        'winding_temp_fault': 'Falla Temp. Devanado',
        'oil_pressure_high': 'Presión Aceite Alta',
        'oil_pressure_low': 'Presión Aceite Baja',
        'h2_high': 'Hidrógeno Alto',
        'h2_low': 'Hidrógeno Bajo',
        'ch4_high': 'Metano Alto',
        'c2h6_high': 'Etano Alto',
        'c2h2_high': 'Acetileno Alto',
        'water_in_oil_alert': 'Nivel de Agua en Aceite (Alerta)',
        'water_in_oil_fault': 'Nivel de Agua en Aceite (Falla)',
        'pump1_fault': 'Falla Bomba 1',
        'pump2_fault': 'Falla Bomba 2',
        'pump1_manual_stop': 'Parada Manual B1',
        'pump2_manual_stop': 'Parada Manual B2',
        'pump3_manual_stop': 'Parada Manual B3',
        'pressure_in_high': 'Presión Entrada Alta',
        'pressure_in_low': 'Presión Entrada Baja',
        'pressure_out_high': 'Presión Salida Alta',
        'pressure_out_low': 'Presión Salida Baja',
        'flow_in_high': 'Flujo Entrada Alto',
        'flow_in_low': 'Flujo Entrada Bajo',
        'flow_out_high': 'Flujo Salida Alto',
        'flow_out_low': 'Flujo Salida Bajo',
        'flood': 'Inundación',
        'humidity_low': 'Humedad Baja',
        'humidity_high': 'Humedad Alta',
        
        // Battery Faults
        'fault': 'Falla General',
        'current_high': 'Corriente Alta',
        'input_voltage_low': 'Voltaje Entrada Bajo',
        'output_voltage_low': 'Voltaje Salida Bajo',
        
        // Substation Faults
        'temp_high': 'Temperatura Alta',
        'temp_low': 'Temperatura Baja',
        'frequency_high': 'Frecuencia Alta',
        'frequency_low': 'Frecuencia Baja'
    };

    const eventConfiguration = {
        T3: {
            General: ['overload', 'cooling_fault'],
            Temperaturas: ['transformer_temp_high', 'oil_temp_alert', 'oil_temp_fault', 'winding_temp_alert', 'winding_temp_fault'],
            'Presión Aceite': ['oil_pressure_high', 'oil_pressure_low'],
            HYDRAN: ['h2_high', 'h2_low', 'ch4_high', 'c2h6_high', 'c2h2_high', 'water_in_oil_alert', 'water_in_oil_fault'],
            Bombas: ['pump1_fault', 'pump2_fault', 'pump1_manual_stop', 'pump2_manual_stop', 'pump3_manual_stop'],
            Agua: ['pressure_in_high', 'pressure_in_low', 'pressure_out_high', 'pressure_out_low', 'flow_in_high', 'flow_in_low', 'flow_out_high', 'flow_out_low', 'flood', 'humidity_low', 'humidity_high']
        },
        T4: {
            General: ['overload', 'cooling_fault'],
            Temperaturas: ['transformer_temp_high', 'oil_temp_alert', 'oil_temp_fault', 'winding_temp_alert', 'winding_temp_fault'],
            'Presión Aceite': ['oil_pressure_high', 'oil_pressure_low'],
            HYDRAN: ['h2_high', 'h2_low', 'ch4_high', 'c2h6_high', 'c2h2_high', 'water_in_oil_alert', 'water_in_oil_fault'],
            Bombas: ['pump1_fault', 'pump1_manual_stop', 'pump2_manual_stop', 'pump3_manual_stop'],
            Agua: ['pressure_in_high', 'pressure_in_low', 'pressure_out_high', 'pressure_out_low', 'flow_in_high', 'flow_in_low', 'flow_out_high', 'flow_out_low', 'flood', 'humidity_low', 'humidity_high']
        },
        BATTERY: {
            General: ['fault', 'current_high', 'input_voltage_low', 'output_voltage_low']
        },
        SUBSTATION: {
            General: ['temp_high', 'temp_low', 'frequency_high', 'frequency_low']
        }
    };

    function createEventButtons() {
        for (const [target, groups] of Object.entries(eventConfiguration)) {
            const targetPane = document.getElementById(target.toLowerCase());
            if (!targetPane) continue;

            let content = '';
            for (const [groupName, events] of Object.entries(groups)) {
                content += `<div class="button-group"><h5>${groupName}</h5>`;
                events.forEach(event => {
                    const buttonText = translationMap[event] || event.replace(/_/g, ' ');
                    content += `<button class="btn btn-outline-secondary event-btn" data-event="${target}_${event}">${buttonText}</button>`;
                });
                content += '</div>';
            }
            targetPane.innerHTML = content;
        }
    }

    function logMessage(message, type = 'info') {
        const timestamp = `[${new Date().toLocaleTimeString()}]`;
        const typePrefix = type.toUpperCase();
        logOutput.textContent += `${timestamp} [${typePrefix}] ${message}\n`;
        logOutput.scrollTop = logOutput.scrollHeight;
    }

    function updateUI(status) {
        const { simulation_running, active_events } = status;

        startBtn.disabled = simulation_running;
        stopBtn.disabled = !simulation_running;
        intervalInput.disabled = simulation_running;

        let totalActiveEvents = 0;
        Object.values(active_events).forEach(target_events => {
            totalActiveEvents += Object.keys(target_events).length;
        });

        if (simulation_running) {
            statusIndicator.className = totalActiveEvents > 0 ? 'event' : 'running';
            statusText.textContent = totalActiveEvents > 0 ? `Estado: En ejecución (con ${totalActiveEvents} evento/s activo/s)` : 'Estado: En ejecución (Operación Normal)';
        } else {
            statusIndicator.className = 'stopped';
            statusText.textContent = 'Estado: Detenido';
        }

        document.querySelectorAll('.event-btn').forEach(button => {
            const event = button.getAttribute('data-event');
            const [target, ...event_type_parts] = event.split('_');
            const event_type = event_type_parts.join('_');
            if (active_events[target] && active_events[target][event_type]) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });

        updateDeviceStatus(simulation_running);
    }

    function updateDeviceStatus(isRunning) {
        const devices = ['T3', 'T4', 'Baterías', 'General'];
        deviceStatusList.innerHTML = '';
        devices.forEach(device => {
            const li = document.createElement('li');
            li.className = 'list-group-item';
            const statusSpan = document.createElement('span');
            statusSpan.className = `status-dot ${isRunning ? 'running' : 'stopped'}`;
            li.appendChild(statusSpan);
            li.append(` ${device}`);
            deviceStatusList.appendChild(li);
        });
    }

    async function fetchStatus() {
        try {
            const response = await fetch('/api/status');
            if (!response.ok) throw new Error('No se pudo conectar con el servidor.');
            const status = await response.json();
            updateUI(status);
        } catch (error) {
            console.error('Error fetching status:', error);
            updateUI({ simulation_running: false, active_events: {} });
            statusText.textContent = 'Estado: Desconectado';
            statusIndicator.className = 'stopped';
        }
    }

    startBtn.addEventListener('click', () => {
        const interval = intervalInput.value;
        fetch('/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ interval: interval })
        })
        .then(response => response.json().then(data => ({ ok: response.ok, data })))
        .then(({ ok, data }) => {
            if (!ok) throw new Error(data.message);
            logMessage(data.message);
            fetchStatus();
        })
        .catch(error => {
            logMessage(error.message, 'error');
            fetchStatus();
        });
    });

    stopBtn.addEventListener('click', () => {
        fetch('/stop', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                logMessage(data.message);
                fetchStatus();
            })
            .catch(error => {
                logMessage(error.message, 'error');
                fetchStatus();
            });
    });

    eventTabsContent.addEventListener('click', (e) => {
        if (e.target.classList.contains('event-btn')) {
            const event = e.target.getAttribute('data-event');
            fetch('/trigger_event', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ event: event })
            })
            .then(response => response.json().then(data => ({ ok: response.ok, data })))
            .then(({ ok, data }) => {
                if (!ok) throw new Error(data.message);
                logMessage(data.message);
                fetchStatus();
            })
            .catch(error => {
                logMessage(error.message, 'error');
            });
        }
    });

    document.getElementById('clear-all-events').addEventListener('click', () => {
        fetch('/trigger_event', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ event: "none" })
        })
        .then(response => response.json().then(data => ({ ok: response.ok, data })))
        .then(({ ok, data }) => {
            if (!ok) throw new Error(data.message);
            logMessage(data.message);
            fetchStatus();
        })
        .catch(error => {
            logMessage(error.message, 'error');
        });
    });

    createEventButtons();
    logMessage("Simulador listo para iniciar.");
    fetchStatus();
    setInterval(fetchStatus, 2000);
});