# app_state.py

import threading
from collections import deque

ser = None
app_running = True
data_lock = threading.Lock()

wave_running = False
sismo_running = False

x_data = deque(maxlen=500); y_data = deque(maxlen=500)
expected_wave_data = deque(maxlen=500); plot_start_time = 0; max_points = 500

log_recv = deque(maxlen=100); log_sent = deque(maxlen=100); log_dirty = False

viewer_seismic_files = {}           # Files and their traces for the viewer
viewer_all_traces = []              # Flat list of all traces
viewer_selected_trace_index = None  # Index of the selected trace
viewer_data_dirty = threading.Event() # Event to notify GUI to update viewer

viewer_playback_status = "Idle"
viewer_playback_status_dirty = False
viewer_playback_amplitude = 1600
viewer_playback_start_time = 0.0
viewer_playback_paused = False
viewer_playback_time_bounds = (0.0, 0.0)
