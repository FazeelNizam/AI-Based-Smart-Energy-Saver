import tkinter as tk
from tkinter import ttk
import threading
from flask import Flask, jsonify
import time
from datetime import datetime

# --- Flask Web Server Setup ---
app = Flask(__name__)

# Global State (Shared between GUI and Server)
current_state = {
    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    'hour': 12,
    'minute': 0,
    'appliances': {},
    'total_watts': 0
}

@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(current_state)

def run_server():
    app.run(port=5000, debug=False, use_reloader=False)

# --- GUI Controller ---
class SmartHomeSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Home Control Panel (Server)")
        self.root.geometry("500x600")
        
        # Appliance Configuration
        self.appliances_config = {
            'Living Room AC': 1200, 'Living Room TV': 120, 'Living Room Light': 15,
            'Kitchen Oven': 2500, 'Kitchen Fridge': 700, 'Kitchen Light': 30,
            'Bedroom 1 AC': 800, 'Bedroom 1 PC': 560, 'Bedroom 1 Light': 30,
            'Bedroom 2 AC': 800, 'Bedroom 2 TV': 80, 'Bedroom 2 Light': 15,
            'Bathroom 1 Heater': 8000, 'Bathroom 2 Heater': 8000, 
            'Washing Machine': 1200, 'Outdoor Lights': 80
        }
        
        self.switches = {} # Holds Tkinter variables
        
        self.setup_ui()
        self.update_loop()

    def setup_ui(self):
        # 1. Time Control
        frame_time = tk.LabelFrame(self.root, text="Time Simulation", padx=10, pady=10)
        frame_time.pack(fill="x", padx=10, pady=5)
        
        tk.Label(frame_time, text="Hour (0-23):").pack(anchor="w")
        self.slider_hour = tk.Scale(frame_time, from_=0, to=23, orient="horizontal")
        self.slider_hour.set(12)
        self.slider_hour.pack(fill="x")
        
        # 2. Appliance Switches
        frame_apps = tk.LabelFrame(self.root, text="Manual Switches", padx=10, pady=10)
        frame_apps.pack(fill="both", expand=True, padx=10, pady=5)
        
        for name, watts in self.appliances_config.items():
            var = tk.IntVar()
            cb = tk.Checkbutton(frame_apps, text=f"{name} ({watts}W)", variable=var, font=("Arial", 10))
            cb.pack(anchor="w")
            self.switches[name] = var

        # 3. Status Output
        self.lbl_total = tk.Label(self.root, text="Total Output: 0 W", font=("Arial", 14, "bold"), fg="red")
        self.lbl_total.pack(pady=10)
        
        tk.Label(self.root, text="Server running at http://127.0.0.1:5000/data", fg="blue").pack()

    def update_loop(self):
        # Calculate Total Power
        total_w = 0
        app_status = {}
        
        for name, var in self.switches.items():
            is_on = var.get()
            watts = self.appliances_config[name]
            if is_on:
                total_w += watts
            app_status[name] = "ON" if is_on else "OFF"

        # Update Global State for Server
        sim_hour = self.slider_hour.get()
        sim_time = datetime.now().replace(hour=sim_hour, minute=0, second=0)
        
        current_state['timestamp'] = sim_time.strftime("%Y-%m-%d %H:%M:%S")
        current_state['hour'] = sim_hour
        current_state['minute'] = 0
        current_state['day_of_week'] = sim_time.weekday()
        current_state['appliances'] = app_status
        current_state['total_watts'] = total_w

        # Update GUI Label
        self.lbl_total.config(text=f"Streaming: {total_w} W")
        
        self.root.after(500, self.update_loop)

if __name__ == "__main__":
    # Start Flask in a separate thread
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
    
    # Start GUI
    root = tk.Tk()
    app_gui = SmartHomeSimulator(root)
    root.mainloop()
    