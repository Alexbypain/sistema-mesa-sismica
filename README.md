# 🌋 **Replica**
## sistema de control para mesa sismica 
 ![LICENSE](https://www.gnu.org/graphics/agplv3-88x31.png)
 
software para el control de mesa sismica, que permite aprovechar la informacion publica que sobre los sismos

Aquí tienes un **README.md** listo para tu repositorio. Puedes copiarlo tal cual y adaptarlo si cambias pines, nombres de carpetas o licencias. 

---

# Mesa Sísmica de Bajo Costo con Control y GUI

Sistema de **reproducción de acelerogramas reales** en una mesa sísmica de laboratorio. Convierte registros aceleración–tiempo en trayectorias de **posición** y las ejecuta en tiempo real mediante un **ESP32**, un **driver microstepping** y **realimentación** con encoder magnético **AS5600**. Incluye **interfaz gráfica** para cargar señales, monitorear la respuesta y operar la mesa.

## ✨ Características

* 📥 **Importación de registros sísmicos** (formato CSV/ASCII) y preprocesamiento.
* 🔁 **Transformación** a posición (filtrado + doble integración + escalado mecánico).
* 🧠 **Control**: abierto (rampas/ondas) y lazo cerrado preliminar con PID.
* 🧰 **GUI** para carga de señales, control de ejecución, gráficos en tiempo real.
* 🔌 **Hardware económico** y replicable (ESP32 + driver + motor + encoder).

## 🧱 Arquitectura del Sistema

```
Acelerograma (a-t) --> Filtro/normalización --> ∫∫ --> Posición(t) --> Generador de pulsos
                                                            |                       |
                                                            v                       v
                                                        ESP32 (STEP/DIR, PID) --> Driver --> Motor --> Mesa
                                                                 |                                     ^
                                                                 v                                     |
                                                            Encoder AS5600  <------ Telemetría ---------
```

## 🛒 Bill of Materials (BoM)

* Control: **ESP32** DevKit (WROOM o S3).
* Driver de motor: **DM542T** (recomendado) o equivalente microstepping robusto.
* Motor: **NEMA 23/24** (según carga y carrera).
* Sensor: **AS5600** (encoder magnético) + imán diametral.
* Fuente DC: **24–48 V**, corriente según motor (≥ 4–6 A típico).
* Mecánica: rieles lineales, husillo/correa, mesa/plataforma, topes y guarda.

> ⚠️ Ajusta la selección según masa máxima en la mesa, carrera útil y aceleraciones objetivo.

## 🧩 Estructura del Repositorio

```
.
├── firmware/
│   ├── src/                # Código ESP32 (Arduino/ESP-IDF)
│   └── config.h            # Pines, pasos por vuelta, límites, PID
├── gui/
│   ├── requirements.txt    # Dependencias Python
│   └── app.py              # Interfaz gráfica y pipeline de señales
├── data/
│   ├── samples/            # Acelerogramas de ejemplo
│   └── outputs/            # Trayectorias generadas y logs
├── docs/
│   ├── wiring.pdf          # Esquemático/conexiones
│   └── figures/            # Imágenes para el README/Informe
└── README.md
```

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

Si usas este proyecto en tu trabajo académico, cita el repositorio y las fuentes de hardware/teoría (por ejemplo, textos de dinámica estructural y documentación de sensores/actuadores que utilices).

## 🤝 Contribuciones

¡PRs bienvenidos! Abre un **issue** con: descripción, logs, versión de firmware/GUI, esquema de conexiones y archivos de prueba mínimos.

## 📄 Licencia

Indica aquí tu licencia (p. ej., MIT, Apache-2.0 o CC BY-NC-SA).
`SPDX-License-Identifier: MIT`

## 📨 Contacto

* Autor/es: *[tu nombre y correo]*
* Lab/Universidad: *[tu institución]*
* Dudas técnicas: issues del repositorio

---

> Sugerencia: añade a `docs/` un **esquemático** (PDF/PNG), una **foto del montaje** y un **GIF** corto de la mesa ejecutando un acelerograma para que tu README luzca aún mejor.
