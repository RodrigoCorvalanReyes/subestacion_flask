import sqlite3

DB_FILE = "mqtt_configs.db"

def init_db():
    """Inicializa la base de datos y la tabla si no existen."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Crear tabla
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mqtt_configurations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note TEXT NOT NULL UNIQUE,
                broker TEXT NOT NULL,
                port INTEGER NOT NULL,
                topic TEXT NOT NULL,
                username TEXT
            )
        ''')

        # Verificar si la tabla está vacía para agregar la configuración por defecto
        cursor.execute("SELECT COUNT(*) FROM mqtt_configurations")
        if cursor.fetchone()[0] == 0:
            print("Base de datos vacía, insertando configuración por defecto.")
            default_config = (
                '', 
                '', 
                , 
                '', 
                ''
            )
            cursor.execute("INSERT INTO mqtt_configurations (note, broker, port, topic, username) VALUES (?, ?, ?, ?, ?)", default_config)
            print("Configuración por defecto guardada.")

        conn.commit()
        print("Base de datos inicializada correctamente.")
    except sqlite3.Error as e:
        print(f"Error al inicializar la base de datos: {e}")
    finally:
        if conn:
            conn.close()

def add_config(note, broker, port, topic, username):
    """Agrega una nueva configuración MQTT a la base de datos."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO mqtt_configurations (note, broker, port, topic, username) VALUES (?, ?, ?, ?, ?)", (note, broker, port, topic, username))
        conn.commit()
        return {"success": True, "id": cursor.lastrowid}
    except sqlite3.IntegrityError:
        return {"success": False, "error": f"Ya existe una configuración con la nota '{note}'."}
    except sqlite3.Error as e:
        return {"success": False, "error": str(e)}
    finally:
        if conn:
            conn.close()

def get_all_configs():
    """Obtiene todas las configuraciones MQTT de la base de datos."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row # Devuelve filas como diccionarios
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mqtt_configurations ORDER BY note ASC")
        rows = cursor.fetchall()
        # Convertir las filas a diccionarios estándar
        configs = [dict(row) for row in rows]
        return configs
    except sqlite3.Error as e:
        print(f"Error al obtener configuraciones: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_config_by_id(config_id):
    """Obtiene una configuración específica por su ID."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mqtt_configurations WHERE id = ?", (config_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"Error al obtener la configuración {config_id}: {e}")
    finally:
        if conn:
            conn.close()

def delete_config(config_id):
    """Elimina una configuración de la base de datos por su ID."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM mqtt_configurations WHERE id = ?", (config_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return {"success": True, "message": "Configuración eliminada con éxito."}
        else:
            return {"success": False, "error": "No se encontró ninguna configuración con ese ID."}
    except sqlite3.Error as e:
        return {"success": False, "error": str(e)}
    finally:
        if conn:
            conn.close()
