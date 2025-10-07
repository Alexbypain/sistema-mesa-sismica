
 ![LICENSE](https://www.gnu.org/graphics/agplv3-88x31.png) 
# Mesa Sísmica de Bajo Costo con Control y GUI

Sistema de **reproducción de acelerogramas reales** en una mesa sísmica de laboratorio. Convierte registros aceleración–tiempo en trayectorias de **posición** y las ejecuta en tiempo real mediante un **ESP32**, un **driver microstepping** y **realimentación** con encoder magnético **AS5600**. Incluye **interfaz gráfica** para cargar señales, monitorear la respuesta y operar la mesa.

## ✨ Características

* 📥 **Importación de registros sísmicos** (formato CSV/ASCII) y preprocesamiento.
* 🔁 **Transformación** a posición (filtrado + doble integración + escalado mecánico).
* 🧠 **Control**: abierto (rampas/ondas) y lazo cerrado preliminar con PID.
* 🧰 **GUI** para carga de señales, control de ejecución, gráficos en tiempo real.
* 🔌 **Hardware económico** y replicable (ESP32 + driver + motor + encoder).

## 🧱 Diagrama flujo

```mermaid
graph TD
    subgraph PC["App"]
        A[Acelerograma a-t] --> B[Filtro/Normalización]
        B --> C[Integración Doble ∫∫]
        C --> D[Desplazamiento Deseado x_ref]
        D --> CMD[Generación de Comandos STEP/DIR]
        F[Monitor/Visualización]
        POS[Posición Real x_actual] --> F
        D --> F
    end
    
    CMD -->|Serial/USB| G
    
    subgraph Mesa["Mesa Sísmica"]
        G[ESP32 Controlador]
        K[Encoder AS5600]
        GEN[Generador Pulsos STEP/DIR]
        H[Driver Motor Stepper]
        I[Motor Paso a Paso]
        J[Actuador/Mesa]
       
        G -->|Comandos| GEN
        GEN -->|STEP + DIR| H
        H -->|Corriente| I
        I -->|Movimiento| J
        J -->|Rotación Eje| K
        K -->|I2C SDA/SCL GPIO21/22| G
        G -->|Feedback Serial| POS
    end
```
## 🧱 Diagrama de Clases 
```mermaid
classDiagram
    class app_state {
        <<module>>
        +data_lock threading.Lock
        +list x_data
        +list y_data
        +list expected_wave_data
        +list log_recv
        +list log_sent
        +bool log_dirty
        +bool wave_running
        +bool app_running
        +float plot_start_time
        +int max_points
        +dict viewer_seismic_files
        +list viewer_all_traces
        +int viewer_selected_trace_index
        +threading.Event viewer_data_dirty
    }

    class main {
        <<module>>
        +create_gui()
        +update_gui_callbacks()
        +cleanup()
        +main()
        -update_ui_for_connection_state(bool)
        -checkbox_callback()
        -connect_callback()
        -disconnect_callback()
        -refresh_ports_callback()
        -send_manual_command_callback()
        -start_wave_callback()
        -stop_wave_callback()
        -_viewer_on_trace_select()
        -_update_viewer_file_tree()
        -_update_viewer_detailed_plot()
    }

    class serial_handler {
        <<module>>
        +find_serial_ports() list
        +connect_serial(port, baud) tuple
        +disconnect_serial()
        +send_command(command)
        +read_serial_thread()
        +wave_generator_thread()
    }

    class seismic_handler {
        <<module>>
        +RECORDS_FOLDER_NAME str
        +get_records_folder_path() str
        +load_data_for_viewer_thread()
        +process_selected_trace()
    }
    
    main ..> app_state : reads/writes
    main ..> serial_handler : calls
    main ..> seismic_handler : calls

    serial_handler ..> app_state : reads/writes
    seismic_handler ..> app_state : reads/writes
```
## 🧱 Diagrama de casos de uso 
```mermaid
graph LR
    User([👤 Usuario/Operador])
    ESP32([🔌 ESP32 + Encoder AS5600])
    
    subgraph System["Sistema Mesa Sísmica"]
        UC1((Conectar<br/>a ESP32))
        UC2((Desconectar<br/>ESP32))
        UC3((Enviar<br/>Comando Manual))
        UC4((Configurar<br/>Parámetros Motor))
        UC5((Generar<br/>Onda Sinusoidal))
        UC6((Detener<br/>Generación))
        UC7((Cargar<br/>Registros Sísmicos))
        UC8((Seleccionar<br/>Traza Sísmica))
        UC9((Visualizar<br/>Traza Detallada))
        UC10((Procesar<br/>Traza para Mesa))
        UC11((Monitorear<br/>Posición Real))
        UC12((Comparar<br/>Expected vs Real))
    end
    
    User --- UC1
    User --- UC2
    User --- UC3
    User --- UC4
    User --- UC5
    User --- UC6
    User --- UC7
    User --- UC8
    User --- UC9
    User --- UC10
    User --- UC11
    User --- UC12
    
    UC1 -.- ESP32
    UC2 -.- ESP32
    UC3 -.- ESP32
    UC5 -.- ESP32
    UC6 -.- ESP32
    UC11 -.- ESP32
    UC12 -.- ESP32
    
    UC5 -.->|include| UC4
    UC10 -.->|include| UC8
    UC9 -.->|include| UC8
    UC11 -.->|require| UC1
    UC3 -.->|require| UC1
    UC5 -.->|require| UC1
    
```
## 🛒 Bill of Materials (BoM)

* Control: **ESP32** DevKit (WROOM o S3).
* Driver de motor: **DM542T** (recomendado) o equivalente microstepping robusto.
* Motor: **NEMA 23/24** (según carga y carrera).
* Sensor: **AS5600** (encoder magnético) + imán diametral.
* Fuente DC: **24–48 V**, corriente según motor (≥ 4–6 A típico).
* Mecánica: rieles lineales, husillo/correa, mesa/plataforma, topes y guarda.

> ⚠️ Ajusta la selección según masa máxima en la mesa, carrera útil y aceleraciones objetivo.


## 🔧 Conexiones (referencia)

| Señal             | ESP32 Pin  | Driver/AS5600  | Nota                    |
| ----------------- | ---------- | -------------- | ----------------------- |
| STEP              | GPIO **X** | DM542T STEP+/- | Ajustar a tu placa      |
| DIR               | GPIO **Y** | DM542T DIR+/-  | Sentido de giro         |
| ENABLE (opcional) | GPIO **Z** | DM542T ENA+/-  | Activa/desactiva driver |
| AS5600 SDA        | GPIO 21    | SDA            | I²C                     |
| AS5600 SCL        | GPIO 22    | SCL            | I²C                     |
| 5V / 3V3          | 3V3/5V     | AS5600 VCC     | Según módulo            |
| GND               | GND        | Todos          | Masa común              |

> Define los pines reales en `firmware/config.h`.

## 🚀 Puesta en Marcha

### 1) Firmware (ESP32)

1. Instala **Arduino IDE** o **ESP-IDF** con toolchain para ESP32.
2. Abre `firmware/` y configura `config.h`:

   * Pasos por vuelta, **microstep**, relación mecánica (mm/paso o deg/paso).
   * Pines STEP/DIR/ENABLE, límites de viaje, **KP/KI/KD** iniciales.
3. Compila y sube al ESP32.

### 2) GUI (Python)

```bash
cd gui
python -m venv .venv
. .venv/bin/activate   # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
python app.py
```

* Selecciona el **puerto serial** del ESP32.
* Carga un acelerograma (`data/samples/…`), ajusta **filtro** y **escala**.
* Genera la **trayectoria** y ejecuta.
* Observa **referencia vs. respuesta** en tiempo real.

## ⚙️ Configuración de Señales

* **Entrada**: aceleración (m/s² o g) con paso de muestreo conocido.
* **Preprocesado**: detrending/HPF para remover deriva, normalización a la capacidad del actuador.
* **Doble integración**: a → v → x (con filtros para minimizar deriva).
* **Escalado**: convierte x(t) a **pasos** mediante (mm por vuelta / microstep).

## 📊 Pruebas y Validación

* **Ondas de prueba**: seno, rampa, chirp para validar carrera/velocidad.
* **Seguimiento**: error RMS y pico, pérdida de paso (0 si correcto).
* **Temperatura**: monitoreo térmico del driver y motor en cargas prolongadas.
* **Carga**: ensayos con masa representativa y fijaciones seguras.

## 🛡️ Seguridad

* Botón de **emergencia** (corte de potencia del driver).
* **Límites** de software y topes mecánicos.
* Nunca operar sin **guardas** y anclaje del cuerpo de prueba.

## 🧪 Resultados (resumen)

* Conversión estable de acelerogramas → trayectorias de posición.
* GUI operable para **carga, ejecución y visualización**.
* Control en **lazo cerrado** preliminar con **AS5600** y sintonía inicial PID.
* Operación sin pérdida de pasos en perfiles dentro de los límites mecánicos.

## 🗺️ Roadmap

* Migración a **servomotor** + **PID avanzado** (o control en espacio de estados).
* Mejoras de **filtrado** para reducir deriva post integración.
* **Auto–calibración** de encoder / homing robusto.
* Soporte para **múltiples ejes** y perfiles 6-DoF (futuro).
* Exportación de **reportes** (PDF/CSV) con métricas de seguimiento.

## 📚 Citar / Referencias


## 🤝 Contribuciones

¡PRs bienvenidos! Abre un **issue** con: descripción, logs, versión de firmware/GUI, esquema de conexiones y archivos de prueba mínimos.

## 📄 Licencia

Indica aquí tu licencia (p. ej., MIT, Apache-2.0 o CC BY-NC-SA).
`SPDX-License-Identifier: MIT`

## 📨 Contacto

* Autor/es: Juan Sebastian Hernandez
* Lab/Universidad: Universidad Cooperativa de Colombia
