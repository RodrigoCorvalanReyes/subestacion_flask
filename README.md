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

## Descripción de Variables de Simulación

Esta sección detalla cada una de las variables generadas por el simulador.

---

### Transformadores (T3 y T4)

*El prefijo `*` en los nombres de las variables debe reemplazarse por `T3` o `T4`.*

-   `*_cooling_flow_lps` (Litros por segundo): Caudal del sistema de refrigeración por líquido del transformador. Un valor bajo indica una falla.
-   `*_top_oil_temp` (°C): Temperatura del aceite en la parte superior del transformador. Aumenta con la carga y en fallas de refrigeración.
-   `*_winding_temp` (°C): Temperatura de los devanados (bobinas) del transformador. Es uno de los indicadores de temperatura más críticos.
-   `*_transformer_temp` (°C): Temperatura general del cuerpo del transformador.
-   `*_hot_spot_temp` (°C): Temperatura estimada del punto más caliente dentro de los devanados. Se calcula a partir de la temperatura de los devanados.
-   `*_ambient_temp` (°C): Temperatura ambiente alrededor del transformador.
-   `*_ambient_humidity` (%): Humedad relativa del ambiente alrededor del transformador.
-   `*_oil_pressure` (bar): Presión del aceite dieléctrico dentro del transformador.
-   `*_fan_status` (ON/OFF): Estado de los ventiladores de refrigeración. Se activan por alta temperatura.
-   `*_pump_status` (ON/OFF): Estado de la bomba de circulación de aceite. Se activa por un flujo suficiente.
-   `*_tap_changer_position` (Entero): Posición del cambiador de tomas, un dispositivo que ajusta la relación de vueltas del transformador.
-   `*_transformer_load_pct` (%): Porcentaje de la carga actual del transformador respecto a su capacidad nominal.

---

### Cargador de Baterías

-   `battery_voltage_V` (Voltios): Voltaje de salida del banco de baterías. Un voltaje bajo puede indicar una falla.
-   `battery_current_A` (Amperios): Corriente que fluye hacia o desde las baterías. Un valor negativo indica que las baterías se están descargando.
-   `battery_input_voltage_V` (Voltios): Voltaje de entrada de corriente alterna que alimenta al cargador.
-   `battery_output_voltage_V` (Voltios): Voltaje de salida de corriente continua del cargador.
-   `battery_state_of_charge_pct` (%): Porcentaje del estado de carga de las baterías.
-   `battery_temp_C` (°C): Temperatura del banco de baterías.
-   `charger_status` (FLOAT/FAULT): Estado del cargador. `FLOAT` es normal (carga de mantenimiento), `FAULT` indica una falla.

---

### Sensores Generales de la Subestación

-   `room_temp_control` (°C): Temperatura de la sala de control o de equipos.
-   `grid_frequency_Hz` (Hertz): Frecuencia de la red eléctrica. Debe ser muy estable (cercana a 50Hz).
-   `flood_sensor_status` (0/1): Estado del sensor de inundación. `0` es seco, `1` es inundado.
-   `room_humidity` (%): Humedad relativa en la sala de control.

---

### Línea de Agua

-   `water_pressure_psi` (PSI): Presión en la línea de agua del sistema contra incendios o de refrigeración.
-   `flowmeter_lps` (Litros por segundo): Caudal medido en la línea de agua.

---

### Sonda Hydran (Análisis de Gases Disueltos)

Estas variables representan la concentración de diferentes gases disueltos en el aceite del transformador, medidos en porcentaje. Son indicadores clave para el diagnóstico de fallas internas.

-   `h2_concentration_pct` (%): Concentración de Hidrógeno (H2). Un aumento súbito es un fuerte indicador de descargas parciales (corona).
-   `ch4_concentration_pct` (%): Concentración de Metano (CH4). Se asocia con sobrecalentamiento de baja temperatura.
-   `c2h6_concentration_pct` (%): Concentración de Etano (C2H6). También se asocia con sobrecalentamiento.
-   `c2h2_concentration_pct` (%): Concentración de Acetileno (C2H2). Es un gas crítico que casi exclusivamente indica la presencia de arcos eléctricos de alta energía, una falla muy severa.