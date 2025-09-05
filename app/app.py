import serial
import threading
import time
import dearpygui.dearpygui as dpg

ser = serial.Serial("COM4", 921600, timeout=1)

x_data = []
y_data = []
max_points = 200 
t = 0

prev_angle = None
turns = 0
absolute_angle = 0.0

def send_steps(sender, app_data, user_data):
    steps = dpg.get_value("input_steps")
    try:
        steps_int = int(steps)
        ser.write(f"{steps_int}\n".encode("utf-8"))
        print(f"Enviado: {steps_int} pasos")
    except ValueError:
        print("⚠️ Ingresa un número válido")


def read_serial():
    global x_data, y_data, t, prev_angle, turns, absolute_angle
    while True:
        if ser.in_waiting:
            try:
                line = ser.readline().decode("utf-8").strip()
                angle = float(line)  # valor en [0, 365] aprox

                if prev_angle is not None:
                    # Detectar salto 365 -> 0 (una vuelta adelante)
                    if prev_angle > 300 and angle < 50:
                        turns += 1
                    # Detectar salto 0 -> 365 (una vuelta atrás)
                    elif prev_angle < 50 and angle > 300:
                        turns -= 1

                prev_angle = angle
                absolute_angle = turns * 360 + angle

                # Guardar tiempo y posición absoluta
                x_data.append(t)
                y_data.append(absolute_angle)

                if len(x_data) > max_points:
                    x_data = x_data[-max_points:]
                    y_data = y_data[-max_points:]

                t += 1
            except Exception as e:
                print("Error lectura:", e)
        time.sleep(0.01)


def update_plot():
    if x_data and y_data:
        dpg.set_value("series", [x_data, y_data])

        # Ajustar el eje X para que siga corriendo
        if len(x_data) > 1:
            dpg.set_axis_limits("x_axis", x_data[0], x_data[-1])

    dpg.set_frame_callback(dpg.get_frame_count() + 3, update_plot)

dpg.create_context()

with dpg.window(label="Serial Plotter", width=800, height=500):
    dpg.add_input_text(label="Número de pasos", tag="input_steps", default_value="200")
    dpg.add_button(label="Mover motor", callback=send_steps)
    with dpg.plot(label="Plot", height=400, width=700):
        dpg.add_plot_axis(dpg.mvXAxis, label="Tiempo", tag="x_axis")
        with dpg.plot_axis(dpg.mvYAxis, label="Posición absoluta"):
            dpg.add_line_series([], [], label="Ángulo", tag="series")

# Lanzar hilo de lectura
threading.Thread(target=read_serial, daemon=True).start()

# Primer llamado a actualización
dpg.set_frame_callback(1, update_plot)

dpg.create_viewport(title="Serial Plotter", width=800, height=500)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
