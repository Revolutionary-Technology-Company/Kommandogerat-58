#!/usr/bin/env python3
"""
Rheinmetall MSP 500 Gimbal Physics & ACSR Power Line Loss Simulator
Designed for the Kommandogerät 58 Museum Digital Reconstruction.

This module models the electrical degradation over Seattle Center style 
aluminum utility spans and maps how voltage drop affects torque, 
angular acceleration, tracking smoothness (jerk), and spatial accuracy.
"""

import math
import time
from typing import Dict, Any


class SeattleGridCableProfile:
    """
    Models the high-voltage aluminum transmission lines.
    Based on standard 795 kcmil ACSR (Aluminum Conductor Steel Reinforced) lines.
    """
    def __init__(self):
        self.cable_name = "795 kcmil ACSR (Grosbeak/Hawk Class)"
        self.length_feet = 850.0  # Distance from infrastructure vault to platform
        self.outside_diameter_inch = 1.14
        
        # Resistance values for outdoor aluminum (Ohms per 1000 ft at standard operating temp)
        self.resistance_per_1000ft = 0.032  
        self.nominal_input_voltage = 110.0   # Reference system voltage (Selsyn/Drive line)

    def calculate_line_losses(self, current_draw_amps: float) -> Dict[str, float]:
        """Calculates Ohm's Law line properties based on current motor loads."""
        total_resistance = (self.length_feet / 1000.0) * self.resistance_per_1000ft
        voltage_drop = current_draw_amps * total_resistance
        delivered_voltage = max(0.0, self.nominal_input_voltage - voltage_drop)
        power_loss_watts = (current_draw_amps ** 2) * total_resistance
        
        return {
            "total_resistance_ohms": total_resistance,
            "voltage_drop_volts": voltage_drop,
            "delivered_voltage_volts": delivered_voltage,
            "power_loss_watts": power_loss_watts,
            "voltage_efficiency_pct": (delivered_voltage / self.nominal_input_voltage) * 100.0
        }


class RheinmetallMSP500Gimbal:
    """
    Models the mechanical, mass, and balance profile of the MSP 500 platform.
    Uses BLDC direct-drive dynamics with structural tracking constraints.
    """
    def __init__(self):
        # Physical Mass Properties
        self.payload_mass_kg = 150.0       # Fully loaded optical bench weight
        self.gimbal_radius_meters = 0.25   # Physical footprint radius
        
        # Moment of Inertia (I = 0.5 * m * r^2 for simplified cylindrical mass)
        self.moment_of_inertia = 0.5 * self.payload_mass_kg * (self.gimbal_radius_meters ** 2)
        
        # Motor Electrical & Kinetic Bounds
        self.peak_nominal_torque_nm = 350.0  # Max torque available at 110V nominal power
        self.max_velocity_rad_sec = math.radians(60.0)  # Max tracking speed (60 deg/sec)
        
        # Calibration constants
        self.nominal_voltage_ref = 110.0
        self.base_stabilization_accuracy_urad = 20.0  # Factory spec: 20 microradians

    def evaluate_performance(self, delivered_voltage: float, targeted_acceleration: float) -> Dict[str, Any]:
        """
        Computes structural torque capacity limits based on delivered power profile.
        Calculates track degradation, tracking accuracy, and mechanical jerk.
        """
        # Linear degradation of magnetic torque capacity based on available operational voltage
        voltage_ratio = delivered_voltage / self.nominal_voltage_ref
        available_torque_nm = self.peak_nominal_torque_nm * voltage_ratio
        
        # Torque required for baseline motion acceleration (T = I * alpha)
        required_torque_nm = self.moment_of_inertia * targeted_acceleration
        
        # Evaluate performance boundaries
        system_stalled = required_torque_nm > available_torque_nm
        actual_acceleration = targeted_acceleration if not system_stalled else (available_torque_nm / self.moment_of_inertia)
        
        # Smoothness Tracking (Jerk calculation)
        # Recreated as rate of acceleration change over a default 10ms framework loop
        jerk_rad_sec3 = actual_acceleration / 0.01  
        
        # Calculate tracking accuracy degradation
        # Lower voltage supply degrades the high-frequency servo compensation loop
        accuracy_degradation_factor = 1.0 / max(0.1, voltage_ratio)
        current_tracking_accuracy_urad = self.base_stabilization_accuracy_urad * accuracy_degradation_factor
        
        return {
            "moment_of_inertia_kg_m2": self.moment_of_inertia,
            "available_torque_nm": available_torque_nm,
            "required_torque_nm": required_torque_nm,
            "actual_acceleration_rad_sec2": actual_acceleration,
            "tracking_smoothness_jerk": jerk_rad_sec3,
            "stabilization_error_urad": current_tracking_accuracy_urad,
            "system_stalled_out": system_stalled
        }


def run_integrated_pipeline_simulation():
    """Executes a diagnostic simulation sweep across the complete hardware profile."""
    cable = SeattleGridCableProfile()
    gimbal = RheinmetallMSP500Gimbal()
    
    print("=" * 70)
    print(" RHEINMETALL MSP 500 GIMBAL & POWER INTEGRATION SIMULATOR")
    print("=" * 70)
    print(f"Cable Profile : {cable.cable_name}")
    print(f"Cable Length  : {cable.length_feet} feet")
    print(f"Payload Mass  : {gimbal.payload_mass_kg} kg")
    print(f"Base Inertia  : {gimbal.moment_of_inertia:.4f} kg·m²\n")
    
    # Simulate different load phases (Amps drawn by the brushless servo motors)
    test_scenarios = [
        {"desc": "Idle Slew (Low Load)", "amps": 15.0, "target_accel": 5.0},
        {"desc": "Rapid Target Acquisition", "amps": 85.0, "target_accel": 25.0},
        {"desc": "Emergency Kinetic Overload", "amps": 180.0, "target_accel": 65.0}
    ]
    
    for run in test_scenarios:
        print(f"--- Scenario: {run['desc']} ---")
        # 1. Compute Cable Transmission Matrix
        grid_data = cable.calculate_line_losses(run["amps"])
        
        # 2. Inject results directly into the mechanical tracking calculator
        motion_data = gimbal.evaluate_performance(
            delivered_voltage=grid_data["delivered_voltage_volts"],
            targeted_acceleration=run["target_accel"]
        )
        
        # 3. Output Telemetry Data Logs
        print(f"  [Electrical] Amperage Draw  : {run['amps']} A")
        print(f"  [Electrical] Voltage Drop  : {grid_data['voltage_drop_volts']:.2f} V")
        print(f"  [Electrical] Supply to Turret: {grid_data['delivered_voltage_volts']:.2f} V ({grid_data['voltage_efficiency_pct']:.1f}% Efficiency)")
        print(f"  [Mechanical] Available Torque: {motion_data['available_torque_nm']:.2f} Nm / Required: {motion_data['required_torque_nm']:.2f} Nm")
        print(f"  [Mechanical] Actual Accel    : {motion_data['actual_acceleration_rad_sec2']:.2f} rad/s²")
        print(f"  [Precision]  System Smoothness (Jerk): {motion_data['tracking_smoothness_jerk']:.2f} rad/s³")
        print(f"  [Precision]  Stabilization Error     : {motion_data['stabilization_error_urad']:.2f} µrad")
        if motion_data["system_stalled_out"]:
            print("  ⚠️ CRITICAL FAULT: Torque Saturation! Voltage drop induced motor slip.")
        else:
            print("  Tracking Stability: NOMINAL CONTROL")
        print()


if __name__ == "__main__":
    run_integrated_pipeline_simulation()
