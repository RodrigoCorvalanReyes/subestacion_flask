document.addEventListener('DOMContentLoaded', () => {
    // --- Elementos del DOM ---
    const startBtn = document.getElementById('start-sim');
    const stopBtn = document.getElementById('stop-sim');
    // Remove the old triggerBtn and eventSelector since we're using buttons now
    // const triggerBtn = document.getElementById('trigger-event');
    // const eventSelector = document.getElementById('event-selector');
    
    const statusIndicator = document.getElementById('sim-status-indicator');
    const statusText = document.getElementById('sim-status-text');
    const logOutput = document.getElementById('log-output');

    const mqttForm = document.getElementById('mqtt-form');
    const configSelector = document.getElementById('config-selector');
    const deleteConfigBtn = document.getElementById('delete-config');
    const intervalInput = document.getElementById('interval-seconds');

    const activeEventsList = document.getElementById('active-events-list');

    // --- Mapa de Nombres de Eventos ---
    const eventFriendlyNames = {
        'cooling_fault': 'Falla de Refrigeración',
        'overload': 'Sobrecarga',
        'fault': 'Falla del Cargador',
        'flood': 'Sensor de Inundación',
        'oil_pressure_high': 'Presión de Aceite Alta',
        'oil_pressure_low': 'Presión de Aceite Baja',
        'transformer_temp_high': 'Temperatura de Transformador Alta',
        'temp_high': 'Temperatura Alta',
        'temp_low': 'Temperatura Baja',
        'frequency_high': 'Frecuencia de Red Alta',
        'frequency_low': 'Frecuencia de Red Baja',
        'pressure_high': 'Presión de Agua Alta',
        'pressure_low': 'Presión de Agua Baja',
        'flow_high': 'Flujo de Agua Alto',
        'flow_low': 'Flujo de Agua Bajo',
        'h2_high': 'Falla H2',
        'ch4_high': 'Falla CH4',
        'c2h6_high': 'Falla C2H6',
        'c2h2_high': 'Falla C2H2'
    };

    // --- Lógica de la Interfaz ---

    function logMessage(message, type = 'info') {
        const timestamp = `[${new Date().toLocaleTimeString()}]`;
        const typePrefix = type.toUpperCase();
        logOutput.textContent += `${timestamp} [${typePrefix}] ${message}
`;
        logOutput.scrollTop = logOutput.scrollHeight; // Auto-scroll
    }

    function updateUI(status) {
        const { simulation_running, active_events } = status;

        // Actualizar estado de los botones y controles
        startBtn.disabled = simulation_running;
        stopBtn.disabled = !simulation_running;
        configSelector.disabled = simulation_running;
        deleteConfigBtn.disabled = simulation_running;
        intervalInput.disabled = simulation_running;
        document.querySelector('.add-config-details summary').style.pointerEvents = simulation_running ? 'none' : 'auto';

        // Contar eventos activos
        let totalActiveEvents = 0;
        Object.values(active_events).forEach(target_events => {
            totalActiveEvents += Object.keys(target_events).length;
        });

        // Actualizar indicador de estado principal
        if (simulation_running) {
            if (totalActiveEvents > 0) {
                statusIndicator.className = 'event';
                statusText.textContent = `Estado: En ejecución (con ${totalActiveEvents} evento/s activo/s)`;
            } else {
                statusIndicator.className = 'running';
                statusText.textContent = 'Estado: En ejecución (Operación Normal)';
            }
        } else {
            statusIndicator.className = 'stopped';
            statusText.textContent = 'Estado: Detenido';
        }

        // Actualizar lista de eventos activos
        activeEventsList.innerHTML = '';
        if (totalActiveEvents === 0) {
            // Add system status when no events are active
            const statusText = simulation_running ? 'Conectado' : 'Desconectado';
            activeEventsList.innerHTML = `<li>${statusText} - Sin eventos activos</li>`;
        } else {
            for (const [target, events] of Object.entries(active_events)) {
                for (const event_type of Object.keys(events)) {
                    const friendlyName = eventFriendlyNames[event_type] || event_type;
                    // Map target codes to friendly names
                    const targetNames = {
                        'T3': 'T3',
                        'T4': 'T4', 
                        'BATTERY': 'Batería',
                        'SUBSTATION': 'Subestación',
                        'WATERLINE': 'Línea de Agua'
                    };
                    const targetDisplayName = targetNames[target] || target;
                    const li = document.createElement('li');
                    li.textContent = `${targetDisplayName}: ${friendlyName}`;
                    activeEventsList.appendChild(li);
                }
            }
            // Add system connection status when events are active
            const statusText = simulation_running ? 'Conectado' : 'Desconectado';
            const statusLi = document.createElement('li');
            statusLi.textContent = `Sistema: ${statusText}`;
            statusLi.style.fontStyle = 'italic';
            statusLi.style.opacity = '0.7';
            activeEventsList.appendChild(statusLi);
        }
        
        // Update button states based on active events
        document.querySelectorAll('.event-btn').forEach(button => {
            const event = button.getAttribute('data-event');
            
            // Reconstruct the target and event_type properly
            const parts = event.split('_');
            const target_part = parts[0];
            const event_type_part = parts.slice(1).join('_');
            
            if (active_events[target_part] && active_events[target_part][event_type_part]) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
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
            // Si falla la conexión, mostrar estado detenido para evitar inconsistencias
            updateUI({ simulation_running: false, active_events: {} });
            statusText.textContent = 'Estado: Desconectado';
            statusIndicator.className = 'stopped';
        }
    }

    async function loadConfigs() {
        try {
            const response = await fetch('/api/mqtt_configs');
            if (!response.ok) throw new Error('No se pudo obtener la lista de configuraciones.');
            
            const configs = await response.json();
            configSelector.innerHTML = ''; // Limpiar opciones existentes

            if (configs.length === 0) {
                configSelector.innerHTML = '<option disabled value="">No hay configuraciones guardadas</option>';
                deleteConfigBtn.disabled = true;
            } else {
                configs.forEach(config => {
                    const option = document.createElement('option');
                    option.value = config.id;
                    option.textContent = config.note;
                    configSelector.appendChild(option);
                });
                deleteConfigBtn.disabled = false;
            }
        } catch (error) {
            logMessage(error.message, 'error');
        }
    }

    // --- Event Listeners ---

    mqttForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const data = {
            note: document.getElementById('note').value,
            broker: document.getElementById('broker').value,
            port: document.getElementById('port').value,
            topic: document.getElementById('topic').value,
            username: document.getElementById('username').value,
        };

        try {
            const response = await fetch('/api/mqtt_configs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();

            if (!response.ok) throw new Error(result.error || 'Error desconocido al guardar.');

            logMessage(`Configuración '${data.note}' guardada con éxito.`);
            mqttForm.reset();
            document.querySelector('.add-config-details').open = false;
            await loadConfigs();
            configSelector.value = result.id;
        } catch (error) {
            logMessage(error.message, 'error');
        }
    });

    deleteConfigBtn.addEventListener('click', async () => {
        const selectedConfigId = configSelector.value;
        if (!selectedConfigId) {
            logMessage("No hay ninguna configuración seleccionada para eliminar.", "warn");
            return;
        }

        const selectedConfigNote = configSelector.options[configSelector.selectedIndex].text;
        if (confirm(`¿Estás seguro de que quieres eliminar la configuración "${selectedConfigNote}"?`)) {
            try {
                const response = await fetch(`/api/mqtt_configs/${selectedConfigId}`, {
                    method: 'DELETE'
                });
                const result = await response.json();
                if (!response.ok) throw new Error(result.error || 'Error desconocido al eliminar.');
                
                logMessage(`Configuración "${selectedConfigNote}" eliminada con éxito.`);
                loadConfigs();
            } catch (error) {
                logMessage(error.message, 'error');
            }
        }
    });

    startBtn.addEventListener('click', () => {
        const selectedConfigId = configSelector.value;
        if (!selectedConfigId) {
            logMessage("Por favor, seleccione o guarde una configuración MQTT antes de iniciar.", "error");
            return;
        }
        const interval = intervalInput.value;

        fetch('/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ config_id: selectedConfigId, interval: interval })
        })
        .then(response => response.json().then(data => ({ ok: response.ok, data })))
        .then(({ ok, data }) => {
            if (!ok) throw new Error(data.message);
            logMessage(data.message);
            fetchStatus(); // Actualizar estado inmediatamente
        })
        .catch(error => {
            logMessage(error.message, 'error');
            fetchStatus(); // Sincronizar en caso de error
        });
    });

    stopBtn.addEventListener('click', () => {
        fetch('/stop', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                logMessage(data.message);
                fetchStatus(); // Actualizar estado inmediatamente
            })
            .catch(error => {
                logMessage(error.message, 'error');
                fetchStatus(); // Sincronizar en caso de error
            });
    });

    // Event handling for new toggle buttons
    const eventButtons = document.querySelectorAll('.event-btn');
    const clearAllBtn = document.getElementById('clear-all-events');
    
    // Add click event listeners to each event button
    eventButtons.forEach(button => {
        button.addEventListener('click', () => {
            const event = button.getAttribute('data-event');
            
            fetch('/trigger_event', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ event: event })
            })
            .then(response => response.json().then(data => ({ ok: response.ok, data })))
            .then(({ ok, data }) => {
                if (!ok) throw new Error(data.message);
                logMessage(data.message);
                fetchStatus(); // Actualizar estado inmediatamente
            })
            .catch(error => {
                logMessage(error.message, 'error');
            });
        });
    });
    
    // Add click event listener to clear all events button
    clearAllBtn.addEventListener('click', () => {
        fetch('/trigger_event', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ event: "none" })
        })
        .then(response => response.json().then(data => ({ ok: response.ok, data })))
        .then(({ ok, data }) => {
            if (!ok) throw new Error(data.message);
            logMessage(data.message);
            fetchStatus(); // Actualizar estado inmediatamente
        })
        .catch(error => {
            logMessage(error.message, 'error');
        });
    });

    // --- Inicialización ---
    logMessage("Simulador listo. Seleccione una configuración y presione 'Iniciar Simulación'.");
    loadConfigs();
    fetchStatus(); // Cargar estado inicial
    setInterval(fetchStatus, 2000); // Iniciar sondeo de estado
});