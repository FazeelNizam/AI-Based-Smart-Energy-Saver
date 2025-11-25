import tkinter as tk
from tkinter import messagebox
import requests
import joblib
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

# --- Electricity Pricing Logic ---
class ElectricityBillCalculator:
    def __init__(self):
        # Domestic Tariff Structure (LKR per kWh)
        self.tiers = [
            (60, 7.85),    # First 60 units
            (90, 10.00),   # Next 30 (61-90)
            (120, 27.75),  # Next 30 (91-120)
            (180, 32.00),  # Next 60 (121-180)
            (float('inf'), 61.00) # Over 180
        ]

    def calculate_bill(self, monthly_kwh):
        remaining_units = monthly_kwh
        total_cost = 0
        prev_limit = 0

        for limit, rate in self.tiers:
            if remaining_units <= 0:
                break
            block_units = min(remaining_units, limit - prev_limit)
            total_cost += block_units * rate
            remaining_units -= block_units
            prev_limit = limit
            
        return total_cost

    def get_marginal_rate(self, current_monthly_kwh):
        for limit, rate in self.tiers:
            if current_monthly_kwh < limit:
                return rate
        return 61.00

# --- Main Dashboard Application ---
class EnergyDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Energy Saver - Cost Monitor")
        self.root.geometry("1000x750")
        
        self.server_url = "http://127.0.0.1:5000/data"
        self.model = None
        self.calculator = ElectricityBillCalculator()
        
        # Simulation State
        self.accumulated_kwh = 0.0
        self.projected_monthly_kwh = 150
        
        self.load_model()
        
        # --- GRAPH DATA ---
        self.step_counter = 0 
        self.x_data = []
        self.y_actual = []
        self.y_pred = []

        self.setup_ui()
        self.poll_server()

    def load_model(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, 'energy_model.pkl')
        if os.path.exists(model_path):
            self.model = joblib.load(model_path)
            print("Model loaded.")
        else:
            self.model = None
            print("Model not found")

    def setup_ui(self):
        # Styling
        bg_color = "#f4f6f7"
        self.root.configure(bg=bg_color)

        # Header
        header = tk.Label(self.root, text="Smart Home Energy & Cost Monitor", font=("Segoe UI", 20, "bold"), bg=bg_color, fg="#2c3e50")
        header.pack(pady=15)
        
        # 1. Info Panel
        frame_info = tk.Frame(self.root, bg="#dfe6e9", pady=5)
        frame_info.pack(fill="x", padx=20)
        
        self.lbl_time = tk.Label(frame_info, text="Time: --:--", font=("Consolas", 12), bg="#dfe6e9")
        self.lbl_time.pack(side="left", padx=10)
        
        self.lbl_status = tk.Label(frame_info, text="Connecting...", fg="gray", bg="#dfe6e9")
        self.lbl_status.pack(side="right", padx=10)

        # 2. Main Metrics
        frame_metrics = tk.Frame(self.root, bg=bg_color, pady=10)
        frame_metrics.pack()
        
        # Power Box
        f1 = tk.LabelFrame(frame_metrics, text="Live Power Usage", font=("Segoe UI", 11, "bold"), bg="white", padx=20, pady=10)
        f1.grid(row=0, column=0, padx=15)
        self.lbl_actual = tk.Label(f1, text="0 W", font=("Segoe UI", 28, "bold"), fg="#2980b9", bg="white")
        self.lbl_actual.pack()
        self.lbl_pred = tk.Label(f1, text="Exp: 0 W", font=("Segoe UI", 11), fg="#7f8c8d", bg="white")
        self.lbl_pred.pack()

        # Cost Box
        f2 = tk.LabelFrame(frame_metrics, text="Est. Hourly Cost", font=("Segoe UI", 11, "bold"), bg="white", padx=20, pady=10)
        f2.grid(row=0, column=1, padx=15)
        self.lbl_cost_hr = tk.Label(f2, text="LKR 0.00", font=("Segoe UI", 28, "bold"), fg="#c0392b", bg="white")
        self.lbl_cost_hr.pack()
        self.lbl_tier = tk.Label(f2, text="Tier: Low", font=("Segoe UI", 11), fg="#7f8c8d", bg="white")
        self.lbl_tier.pack()

        # 3. Insights Panel
        frame_tips = tk.LabelFrame(self.root, text="AI Insights", font=("Segoe UI", 12, "bold"), bg="white", fg="#27ae60", padx=15, pady=10)
        frame_tips.pack(fill="x", padx=20, pady=10)
        
        self.lbl_tip_main = tk.Label(frame_tips, text="System initialized...", font=("Segoe UI", 12), bg="white", fg="#2c3e50")
        self.lbl_tip_main.pack(anchor="w")
        
        self.lbl_tip_cost = tk.Label(frame_tips, text="--", font=("Segoe UI", 11, "bold"), bg="white", fg="#d35400")
        self.lbl_tip_cost.pack(anchor="w")

        # 4. Live Graph (Improved Styling)
        self.fig, self.ax = plt.subplots(figsize=(8, 4), dpi=100)
        self.fig.patch.set_facecolor(bg_color) # Match background
        self.ax.set_facecolor("white")
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=10)

    def generate_smart_tip(self, actual_w, pred_w, hour, appliances):
        marginal_rate = self.calculator.get_marginal_rate(self.projected_monthly_kwh)
        hourly_cost = (actual_w / 1000) * marginal_rate
        
        self.lbl_cost_hr.config(text=f"LKR {hourly_cost:.2f}")
        self.lbl_tier.config(text=f"Rate: LKR {marginal_rate}/kWh")

        diff = actual_w - pred_w
        tip_text = "Usage is stable."
        saving_text = ""

        if diff > 500:
            excess_kwh = diff / 1000
            waste_cost = excess_kwh * marginal_rate
            on_apps = [k for k,v in appliances.items() if v == "ON"]
            culprit = on_apps[0] if on_apps else "Unknown"
            tip_text = f"⚠️ High Usage Alert! {culprit} is ON."
            saving_text = f"📉 Turn off to save LKR {waste_cost:.2f} / hr"
        elif appliances.get('Living Room AC') == 'ON' and (10 <= hour < 16):
            cost_per_hr = 1.2 * marginal_rate
            tip_text = "💡 Efficiency Tip: Use fans instead of AC during the day."
            saving_text = f"💰 Potential Saving: LKR {cost_per_hr:.2f} / hr"
        elif (18 <= hour <= 22) and actual_w > 2000:
             tip_text = "⚡ Peak Hour Warning (18:30-22:30). High rates apply."
             saving_text = "Avoid using Washing Machine now."
        elif actual_w < pred_w and actual_w > 0:
            saved_money = ((pred_w - actual_w)/1000) * marginal_rate
            tip_text = "✅ Efficient! Usage is below expected baseline."
            saving_text = f"You are saving ~LKR {saved_money:.2f} / hr"

        self.lbl_tip_main.config(text=tip_text)
        self.lbl_tip_cost.config(text=saving_text)

    def poll_server(self):
        try:
            response = requests.get(self.server_url, timeout=0.5) # Lower timeout
            if response.status_code == 200:
                data = response.json()
                self.update_dashboard(data)
                self.lbl_status.config(text="● Live Stream", fg="green")
            else:
                self.lbl_status.config(text="⚠ Data Error", fg="red")
        except:
            self.lbl_status.config(text="⚠ Server Offline", fg="red")
        
        # Refresh every 1000ms (1 second)
        self.root.after(1000, self.poll_server)

    def update_dashboard(self, data):
        actual_w = data['total_watts']
        hour = data['hour']
        minute = data['minute']
        day = data.get('day_of_week', 0)
        apps = data['appliances']
        
        pred_w = 0
        if self.model:
            pred_w = self.model.predict([[hour, minute, day]])[0]

        # Update GUI Labels
        self.lbl_time.config(text=f"Simulated Time: {hour:02d}:{minute:02d}")
        self.lbl_actual.config(text=f"{actual_w} W")
        self.lbl_pred.config(text=f"Exp: {pred_w:.0f} W")
        
        self.generate_smart_tip(actual_w, pred_w, hour, apps)

        # --- UPDATE GRAPH DATA ---
        self.step_counter += 1  # Increment Counter
        self.x_data.append(self.step_counter) # Use counter, NOT len()
        self.y_actual.append(actual_w)
        self.y_pred.append(pred_w)

        # Keep last 30 points
        if len(self.x_data) > 30:
            self.x_data.pop(0)
            self.y_actual.pop(0)
            self.y_pred.pop(0)

        # Draw Graph
        self.ax.clear()
        
        # Plot Actual (Blue Line + Fill)
        self.ax.plot(self.x_data, self.y_actual, color="#2980b9", linewidth=2, label='Actual')
        self.ax.fill_between(self.x_data, self.y_actual, color="#2980b9", alpha=0.1)
        
        # Plot Predicted (Green Dashed)
        self.ax.plot(self.x_data, self.y_pred, color="#27ae60", linestyle='--', linewidth=2, label='AI Expected')
        
        # Styling
        self.ax.legend(loc='upper left')
        self.ax.set_title("Real-time Consumption (Watts)", fontsize=10)
        self.ax.grid(True, linestyle='--', alpha=0.5)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = EnergyDashboard(root)
    root.mainloop()