# AI-Based Smart Energy Saver Assistant

## Project Overview

The Smart Energy Saver Assistant is a mini-project developed for **EEX7340** that demonstrates the use of Machine Learning (AI) and Client-Server architecture for proactive household energy monitoring and cost reduction, specifically tailored to the **Sri Lankan tiered electricity tariff**. The system establishes a "normal" energy usage baseline based on a family's routine and provides real-time alerts and cost estimates when actual consumption deviates from the expected norm.

---

## Architecture

The project operates on a **Client-Server IoT Architecture**:

1.  **Server (`smart_home_server.py`):** Acts as a software-based "Virtual House" (using Flask). It simulates the real-time energy draw (Watts) of all household appliances and broadcasts the current state (time, power, switches) via a local REST API.
2.  **Predictive Model (`energy_model.pkl`):** An **Random Forest Regressor** trained on 30 days of synthetic data that learns the family's non-linear energy consumption patterns (e.g., morning high usage vs. midday low usage).
3.  **Client (`dashboard_client.py`):** The graphical user interface (Tkinter) that:
    * Polls the Server for live data.
    * Feeds the time into the AI model for prediction.
    * Compares **Actual Watts** vs. **AI Predicted Watts** to detect anomalies.
    * Calculates the real-time cost in **LKR** using the specific domestic tariff structure.

---

## Key Features

* **Routine-Based Anomaly Detection:** Uses an AI baseline to distinguish between normal high-power events (like the morning water heater rush) and unexpected waste (like leaving an AC on during an empty house period).
* **Real-Time Cost Visualization:** Converts instantaneous Watts into an estimated **LKR per hour** based on the user's current billing tier.
* **Cost-Aware Feedback Loop:** When an anomaly is detected, the dashboard provides specific, actionable advice (e.g., "Turn off Kitchen Oven") and calculates the exact **monetary saving** in LKR for that action.
* **Detailed Data Generation:** The system models a 5-member family, including specific daily activities (working hours, school-going children, domestic helper schedule), resulting in a highly realistic training dataset.

---
