# gui.py

import dearpygui.dearpygui as dpg
import threading
import time
import numpy as np

import app_state
from serial_handler import (find_serial_ports, connect_serial, disconnect_serial, send_command, wave_generator_thread)

# <<< REMOVED IMPORTS RELATED TO THE DELETED SISMOS LOCALES TAB >>>
# from seismic_handler import ( play_local_sismo_thread, create_waveform_image)

# <<< NEW: Import the viewer handler >>>
import seismic_viewer_handler as svh


RECORDS_FOLDER_NAME = "sismic_records"

# --- Callbacks de la Interfaz ---

def update_ui_for_connection_state(connected: bool):
    """Habilita o deshabilita elementos de la UI según el estado de conexión."""
    if connected:
        dpg.set_value("connection_status", f"Conectado a {app_state.ser.port}")
        dpg.configure_item("connect_button", show=False)
        dpg.configure_item("disconnect_button", show=True)
        # Check if wave control buttons exist before enabling
        if dpg.does_item_exist("start_wave_button"): dpg.enable_item("start_wave_button")
        # Removed "play_sismo_button" as its tab is gone
        if dpg.does_item_exist("command_input"): dpg.enable_item("command_input")
        if dpg.does_item_exist("send_command_button"): dpg.enable_item("send_command_button")
    else:
        dpg.set_value("connection_status", "Desconectado")
        dpg.configure_item("connect_button", show=True)
        dpg.configure_item("disconnect_button", show=False)
        # Check if wave control buttons exist before disabling
        if dpg.does_item_exist("start_wave_button"): dpg.disable_item("start_wave_button")
        if dpg.does_item_exist("stop_wave_button"): dpg.disable_item("stop_wave_button")
        # Removed "play_sismo_button" and "stop_sismo_button" as their tab is gone
        if dpg.does_item_exist("command_input"): dpg.disable_item("command_input")
        if dpg.does_item_exist("send_command_button"): dpg.disable_item("send_command_button")
        refresh_ports_callback()

def connect_callback():
    port = dpg.get_value("ports_combo")
    baud = dpg.get_value("baud_rate_combo")
    if port and baud:
        success, message = connect_serial(port, baud)
        if success:
            update_ui_for_connection_state(True)
            with app_state.data_lock:
                app_state.x_data.clear(); app_state.y_data.clear(); app_state.expected_wave_data.clear()
            app_state.plot_start_time = time.time()
        else:
            dpg.set_value("connection_status", f"Error: {message}")

def disconnect_callback():
    disconnect_serial()
    update_ui_for_connection_state(False)

def refresh_ports_callback():
    # Only try to configure if the combo box exists
    if dpg.does_item_exist("ports_combo"):
        dpg.configure_item("ports_combo", items=find_serial_ports())

def send_manual_command_callback():
    command = dpg.get_value("command_input")
    if command: # Only send if command_input exists and has value
        send_command(command)
        if dpg.does_item_exist("command_input"):
            dpg.set_value("command_input", "")

def start_wave_callback():
    if not app_state.wave_running:
        app_state.wave_running = True
        with app_state.data_lock:
            app_state.x_data.clear(); app_state.y_data.clear(); app_state.expected_wave_data.clear()
        app_state.plot_start_time = time.time()
        # Check if control items exist
        if dpg.does_item_exist("speed_input"): send_command(f"s{dpg.get_value('speed_input')}")
        if dpg.does_item_exist("accel_input"): send_command(f"a{dpg.get_value('accel_input')}")
        
        threading.Thread(target=wave_generator_thread, daemon=True).start()
        
        if dpg.does_item_exist("start_wave_button"): dpg.disable_item("start_wave_button")
        if dpg.does_item_exist("stop_wave_button"): dpg.enable_item("stop_wave_button")

def stop_wave_callback():
    app_state.wave_running = False
    if dpg.does_item_exist("start_wave_button"): dpg.enable_item("start_wave_button")
    if dpg.does_item_exist("stop_wave_button"): dpg.disable_item("stop_wave_button")

# <<< REMOVED CALLBACKS RELATED TO THE DELETED SISMOS LOCALES TAB >>>
# def sismo_selected_callback(sender, app_data, user_data): ...
# def stop_sismo_callback(): ...
# def update_sismo_visual_list(): ...


# <<< START: VIEWER FUNCTIONS >>>

def _viewer_on_trace_select(sender, app_data, user_data):
    """Callback triggered when a trace in the viewer is clicked."""
    app_state.viewer_selected_trace_index = user_data
    _update_viewer_file_tree()
    _update_viewer_detailed_plot()

def _update_viewer_file_tree():
    """Redraws the file list and traces in the left panel of the viewer."""
    if not dpg.does_item_exist("viewer_file_tree"): return
    dpg.delete_item("viewer_file_tree", children_only=True)
    if not app_state.viewer_seismic_files:
        dpg.add_text("No data loaded. Click 'Load Data'.", parent="viewer_file_tree")
        return
    for file_name, traces in app_state.viewer_seismic_files.items():
        # Using a default_open=True for tree_node to show traces immediately
        with dpg.tree_node(label=f"{file_name} ({len(traces)} traces)", parent="viewer_file_tree", default_open=True):
            for trace in traces:
                is_selected = (app_state.viewer_selected_trace_index == trace['global_index'])
                indicator = "▶" if is_selected else " "
                label = f"{indicator} {trace['id']} | SR: {trace['sampling_rate']}Hz"
                dpg.add_button(label=label, width=-1, callback=_viewer_on_trace_select, user_data=trace['global_index'])

def _update_viewer_detailed_plot():
    """Redraws the detailed plot and information in the right panel of the viewer."""
    parent_container = "viewer_detailed_plot_container"
    if not dpg.does_item_exist(parent_container): return
    dpg.delete_item(parent_container, children_only=True)
    if app_state.viewer_selected_trace_index is None:
        dpg.add_text("Select a trace from the list to see details.", parent=parent_container)
        return
    try:
        trace_data = app_state.viewer_all_traces[app_state.viewer_selected_trace_index]
    except IndexError:
        app_state.viewer_selected_trace_index = None
        dpg.add_text("Error: Invalid trace index. Selection reset.", parent=parent_container)
        return
    info = (f"ID: {trace_data['id']}\n"
            f"File: {trace_data['file_name']}\n"
            f"Frequency: {trace_data['sampling_rate']} Hz\n"
            f"Samples: {len(trace_data['data'])}\n"
            f"Max Amplitude: {trace_data['max_amp']:.3e}")
    dpg.add_text(info, parent=parent_container)
    dpg.add_separator(parent=parent_container)
    with dpg.plot(label="Detailed View", height=-50, width=-1, parent=parent_container):
        x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
        with dpg.plot_axis(dpg.mvYAxis, label="Amplitude") as y_axis:
            dpg.add_line_series(trace_data['times'].tolist(), trace_data['data'].tolist(), label=trace_data['id'])
        dpg.fit_axis_data(x_axis)
        dpg.fit_axis_data(y_axis)
    with dpg.group(horizontal=True, parent=parent_container):
        dpg.add_button(label="Process", callback=svh.process_selected_trace, width=180, height=30)
        dpg.add_button(label="Play on Table", tag="viewer_play_button", callback=svh.start_playback, width=180, height=30)
        dpg.add_button(label="Stop", tag="viewer_stop_button", callback=svh.stop_playback, width=120, height=30)
    dpg.add_slider_int(label="Playback Amplitude (steps)",
                       tag="viewer_playback_amplitude_slider",
                       default_value=app_state.viewer_playback_amplitude,
                       min_value=100,
                       max_value=10000,
                       callback=_viewer_amplitude_changed,
                       parent=parent_container)
    dpg.add_text(f"Status: {app_state.viewer_playback_status}",
                 tag="viewer_playback_status_label",
                 parent=parent_container)


def _viewer_amplitude_changed(sender, app_data):
    """Stores the latest amplitude selected by the user for playback."""
    with app_state.data_lock:
        app_state.viewer_playback_amplitude = int(app_data)


# <<< END: VIEWER FUNCTIONS >>>


def update_gui_callbacks():
    """Main GUI update loop. Calls all redraw functions."""
    # Viewer tab updates
    if app_state.viewer_data_dirty.is_set():
        _update_viewer_file_tree()
        _update_viewer_detailed_plot()
        app_state.viewer_data_dirty.clear()

    # <<< REMOVED LOGIC RELATED TO THE DELETED SISMOS LOCALES TAB >>>
    # if app_state.sismo_list_dirty:
    #     update_sismo_visual_list()
    #     dpg.enable_item("import_files_button")
    #     app_state.sismo_list_dirty = False
    # if dpg.does_item_exist("sismo_status"): dpg.set_value("sismo_status", app_state.sismo_status_message)
    # if dpg.does_item_exist("sismo_playback_status"): dpg.set_value("sismo_playback_status", app_state.sismo_playback_status_message)
    
    status_dirty = False
    status_message = ""
    is_playing = False
    with app_state.data_lock:
        if app_state.x_data and app_state.y_data and dpg.does_item_exist("series_real_comp"):
            dpg.set_value("series_real_comp", [list(app_state.x_data), list(app_state.y_data)])
        if app_state.expected_wave_data and dpg.does_item_exist("series_expected_comp"):
            expected_x, expected_y = zip(*app_state.expected_wave_data)
            dpg.set_value("series_expected_comp", [list(expected_x), list(expected_y)])
        
        # Only fit axis data if the plots exist
        if (app_state.y_data or app_state.expected_wave_data) and dpg.does_item_exist("x_axis_comp") and dpg.does_item_exist("y_axis_comp"):
            dpg.fit_axis_data("x_axis_comp")
            dpg.fit_axis_data("y_axis_comp")
        
        if app_state.log_dirty:
            if dpg.does_item_exist("console_recv_output"): dpg.set_value("console_recv_output", "\n".join(app_state.log_recv))
            if dpg.does_item_exist("console_send_output"): dpg.set_value("console_send_output", "\n".join(app_state.log_sent))
            if dpg.does_item_exist("console_recv_container"): dpg.set_y_scroll("console_recv_container", -1.0)
            if dpg.does_item_exist("console_send_container"): dpg.set_y_scroll("console_send_container", -1.0)
            app_state.log_dirty = False

        if app_state.viewer_playback_status_dirty:
            status_dirty = True
            status_message = app_state.viewer_playback_status
            app_state.viewer_playback_status_dirty = False

        is_playing = app_state.sismo_running

    is_connected = bool(app_state.ser and app_state.ser.is_open)

    if dpg.does_item_exist("viewer_play_button"):
        if is_playing or not is_connected:
            dpg.disable_item("viewer_play_button")
        else:
            dpg.enable_item("viewer_play_button")

    if dpg.does_item_exist("viewer_stop_button"):
        if is_playing:
            dpg.enable_item("viewer_stop_button")
        else:
            dpg.disable_item("viewer_stop_button")

    if status_dirty and dpg.does_item_exist("viewer_playback_status_label"):
        dpg.set_value("viewer_playback_status_label", f"Status: {status_message}")

def create_gui():
    dpg.create_context()
    
    with dpg.window(label="Panel de Control", tag="main_window"):
        with dpg.tab_bar():

            # --- CONNECION TAB (Restored) ---
            with dpg.tab(label="Connection"):
                with dpg.group(horizontal=False, width=400):
                    dpg.add_text("Serial Connection Control")
                    dpg.add_separator()
                    dpg.add_text("Serial Port")
                    with dpg.group(horizontal=True):
                        dpg.add_combo(items=[], tag="ports_combo", width=280)
                        dpg.add_button(label="Refresh", callback=refresh_ports_callback)
                    dpg.add_text("Baud Rate")
                    dpg.add_combo(["9600", "57600", "115200", "921600"], tag="baud_rate_combo", default_value="115200", width=200)
                    dpg.add_spacer(height=20)
                    dpg.add_button(label="Connect", tag="connect_button", callback=connect_callback, width=-1, height=40)
                    dpg.add_button(label="Disconnect", tag="disconnect_button", callback=disconnect_callback, width=-1, height=40, show=False)
                    dpg.add_text("Disconnected", tag="connection_status", color=(255, 100, 100))

            # <<< REMOVED: SISMOS LOCALES TAB >>>
            # The entire 'with dpg.tab(label="Sismos Locales (MiniSEED)")' block is gone here.

            # --- VIEWER TAB (New) ---
            with dpg.tab(label="Seismic Trace Viewer"):
                with dpg.group(horizontal=True):
                    with dpg.group(width=500):
                        dpg.add_text("Seismic Trace Selector")
                        dpg.add_button(label="Load Data from 'sismic_records'", 
                                       callback=lambda: threading.Thread(target=svh.load_data_for_viewer_thread, daemon=True).start(), 
                                       width=-1, height=40)
                        dpg.add_separator()
                        with dpg.child_window(tag="viewer_file_tree", border=True):
                            dpg.add_text("Click 'Load Data' to begin.")
                    with dpg.group(width=-1):
                        dpg.add_text("Detailed Trace View")
                        dpg.add_separator()
                        with dpg.child_window(tag="viewer_detailed_plot_container"):
                            dpg.add_text("Select a trace from the list to see details.")
            
            # --- WAVE GENERATOR & LOGS TAB (Restored) ---
            with dpg.tab(label="Wave Generator & Logs"):
                with dpg.group(horizontal=True):
                    with dpg.group(width=300):
                        dpg.add_text("Sine Wave Generator")
                        dpg.add_slider_int(label="Amplitude", tag="amplitude_slider", default_value=1600, min_value=100, max_value=10000)
                        dpg.add_slider_float(label="Frequency", tag="frequency_slider", default_value=0.5, min_value=0.1, max_value=5.0, format="%.2f Hz")
                        dpg.add_separator()
                        dpg.add_text("Motor Settings")
                        dpg.add_input_int(label="Speed (s)", tag="speed_input", default_value=50000)
                        dpg.add_input_int(label="Acceleration (a)", tag="accel_input", default_value=20000)
                        dpg.add_separator()
                        with dpg.group(horizontal=True):
                            dpg.add_button(label="Start Wave", tag="start_wave_button", callback=start_wave_callback, width=-1)
                            dpg.add_button(label="Stop Wave", tag="stop_wave_button", callback=stop_wave_callback, width=-1)
                        dpg.add_separator()
                        dpg.add_text("Manual Control & Send Log")
                        dpg.add_input_text(tag="command_input", hint="Command (e.g., m0)", on_enter=True, callback=send_manual_command_callback)
                        dpg.add_button(label="Send Command", tag="send_command_button", callback=send_manual_command_callback, width=-1)
                        with dpg.child_window(tag="console_send_container", height=-1, border=True):
                            dpg.add_input_text(tag="console_send_output", multiline=True, readonly=True, width=-1, height=-1)
                    with dpg.group(width=-1):
                        dpg.add_text("Movement Comparison (Real-time)")
                        with dpg.plot(label="Comparison", height=250, width=-1):
                            dpg.add_plot_legend()
                            dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag="x_axis_comp")
                            with dpg.plot_axis(dpg.mvYAxis, label="Position (steps)", tag="y_axis_comp"):
                                dpg.add_line_series([], [], label="Expected", tag="series_expected_comp")
                                dpg.add_line_series([], [], label="Real", tag="series_real_comp")
                        dpg.add_text("Received from Table")
                        with dpg.child_window(tag="console_recv_container", height=-1, border=True):
                            dpg.add_input_text(tag="console_recv_output", multiline=True, readonly=True, width=-1, height=-1)

    dpg.create_viewport(title='Modular Seismic Table Controller', width=1200, height=700)
    dpg.set_primary_window("main_window", True)
    dpg.setup_dearpygui()
    update_ui_for_connection_state(False)