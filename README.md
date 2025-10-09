# Simulador de Subestación Virtual

## Descripción del Proyecto

Este proyecto es una aplicación web que simula la telemetría de una subestación eléctrica. Permite generar datos realistas y enviarlos a un broker MQTT, facilitando la prueba y desarrollo de plataformas IoT como ThingsBoard sin necesidad de hardware físico.

La interfaz web proporciona un control total sobre la simulación, incluyendo la capacidad de iniciar/detener el envío de datos, gestionar configuraciones de conexión MQTT y simular fallas en tiempo real.

### Características Principales

- **Panel de Control Web:** Interfaz intuitiva para operar el simulador.
- **Gestión de Conexiones MQTT:** Guarda, selecciona y elimina múltiples perfiles de conexión a brokers MQTT.
- **Simulación de Fallas:** Dispara eventos de falla específicos (ej. sobrecarga, falla de refrigeración) para probar la lógica de alarmas del sistema monitoreado.
- **Modelo de Datos Realista:** Genera una amplia gama de variables para transformadores, cargadores de baterías y sensores generales.
- **Intervalo Configurable:** Ajusta la frecuencia de envío de datos directamente desde la interfaz.
- **Persistencia:** Las configuraciones MQTT se guardan en una base de datos local (SQLite).

## Guía de Instalación y Uso

### Requisitos

- Python 3.6 o superior.

### Instalación

1.  Clona o descarga este repositorio.
2.  Abre una terminal en la carpeta del proyecto.
3.  Instala las dependencias:
    ```bash
    pip install Flask paho-mqtt
    ```

### Uso

1.  Ejecuta la aplicación:
    ```bash
    python app.py
    ```
2.  Abre tu navegador y ve a `http://127.0.0.1:5000`.
3.  **Configura la conexión MQTT:**
    -   Usa el panel "Gestor de Conexiones MQTT" para añadir o seleccionar una configuración.
    -   La aplicación incluye una configuración por defecto para un entorno de prueba.
4.  **Inicia la simulación:**
    -   Ajusta el intervalo de envío (en segundos).
    -   Selecciona una configuración MQTT y haz clic en "Iniciar Simulación".
5.  **Simula fallas:**
    -   En el panel "Disparar Eventos de Falla", selecciona un evento y haz clic en "Disparar Evento".
    -   Para volver a la normalidad, selecciona "-- Operación Normal --".

## Estructura del Proyecto

```
/
├── app.py                 # Servidor web principal (Flask)
├── simulation.py          # Lógica de generación de datos
├── database.py            # Gestión de la base de datos
├── mqtt_configs.db        # Archivo de la base de datos (autogenerado)
├── static/
│   ├── script.js          # Lógica del frontend (JavaScript)
│   └── style.css          # Estilos CSS
├── templates/
│   └── index.html         # Interfaz de usuario (HTML)
└── README.md              # Este archivo
```

## Variables de Simulación

A continuación se detallan las variables generadas por el simulador, con sus rangos de valores exactos extraídos del código fuente.

### Transformadores (T3 y T4)

| Variable | Unidad | Rango Nominal | Rango en Falla | Falla Asociada |
| :--- | :---: | :--- | :--- | :--- |
| `*_transformer_load_pct` | % | `70.2 - 85.8` | `104.5 - 115.5` | Sobrecarga |
| `*_cooling_flow_lps` | L/s | `38.8 - 41.2` | `4.8 - 11.2` | Falla de Refrigeración |
| `*_C2H2_ppm` | ppm | `0.42 - 0.58` | `11.25 - 18.75` | Pico de Acetileno (Arco) |
| `*_top_oil_temp` | °C | `71.08 - 80.25` | `78.72 - 85.28` | Sobrecarga / Falla Refrigeración |
| `*_winding_temp` | °C | `84.02 - 93.8` | `92.16 - 99.84` | Sobrecarga / Falla Refrigeración |
| `*_hot_spot_temp` | °C | `94.02 - 103.8` | `102.16 - 109.84`| Sobrecarga / Falla Refrigeración |
| `*_ambient_temp` | °C | `22.5 - 27.5` | - | - |
| `*_ambient_humidity` | % | `42.5 - 57.5` | - | - |
| `*_oil_pressure` | bar | `1.42 - 1.58` | - | - |
| `*_H2_ppm` | ppm | `10.8 - 13.2` | - | - |
| `*_fan_status` | - | `ON` si temp > 75°C | `ON` | - |
| `*_pump_status` | - | `ON` si flujo > 10 L/s | `OFF` | Falla de Refrigeración |
| `*_tap_changer_position`| - | `1 - 9` (aleatorio) | - | - |

*El prefijo `*` corresponde a `T3` o `T4`.*

### Cargador de Baterías

| Variable | Unidad | Rango Nominal | Rango en Falla | Falla Asociada |
| :--- | :---: | :--- | :--- | :--- |
| `charger_status` | - | `FLOAT` | `FAULT` | Falla del Cargador |
| `battery_voltage_V` | V | `122.5 - 127.5` | `104.5 - 115.5` | Falla del Cargador |
| `battery_current_A` | A | `4.5 - 5.5` | `-18 - -12` | Falla del Cargador |
| `battery_state_of_charge_pct`| % | `96.04 - 99.96` | - | - |
| `battery_temp_C` | °C | `28.5 - 31.5` | - | - |

### Sensores Generales de la Subestación

| Variable | Unidad | Rango Nominal | Rango en Falla | Falla Asociada |
| :--- | :---: | :--- | :--- | :--- |
| `flood_sensor_status` | - | `0` (Seco) | `1` (Inundado) | Inundación |
| `room_temp_control` | °C | `21.34 - 22.66` | - | - |
| `grid_frequency_Hz` | Hz | `49.95 - 50.05` | - | - |