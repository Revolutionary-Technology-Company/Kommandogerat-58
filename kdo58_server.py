"""
Rheinmetall 5.5 cm Gerat 58 Interactive Museum Engine.
Author: CMC Correo Hofstad - USAF

This module maps the 17 operational controls, integrates the mechanical 
pulse oiler, evaluates the pneumatic breech loading steps, calculates live 
ballistic force profiles, and includes the interactive maintenance mode sequence.
"""

import time
import math
import sys
from typing import Dict, Any, Tuple

def calculate_ballistic_force(mass_kg: float, velocity_m_s: float, barrel_len_m: float = 4.2) -> Dict[str, float]:
    """Computes muzzle energy and internal acceleration force profiles."""
    if barrel_len_m <= 0:
        return {"energy_mj": 0.0, "force_kn": 0.0, "force_tons": 0.0}
        
    kinetic_energy_joules = 0.5 * mass_kg * (velocity_m_s ** 2)
    average_force_newtons = kinetic_energy_joules / barrel_len_m
    force_tons = average_force_newtons / 9806.65
    
    return {
        "energy_mj": kinetic_energy_joules / 1_000_000,
        "force_kn": average_force_newtons / 1000,
        "force_tons": force_tons
    }

class MechanicalBallisticCam:
    """Simulates the physical 3D Ballistic Cams (Kurvenkorper) found inside the analog computer."""
    def __init__(self):
        self.muzzle_velocity_m_s = 1050.0
        self.projectile_mass_kg = 2.03

    def read_cam_geometry(self, slant_range_meters: float, target_elevation_deg: float) -> Tuple[float, float]:
        if slant_range_meters <= 0:
            return 0.0, 0.0
            
        el_rad = math.radians(target_elevation_deg)
        time_of_flight_sec = slant_range_meters / (self.muzzle_velocity_m_s * math.cos(el_rad) * 0.92)
        gravity_drop_meters = 0.5 * 9.81 * (time_of_flight_sec ** 2)
        elevation_correction_deg = math.degrees(math.atan2(gravity_drop_meters, slant_range_meters))
        fuze_delay_seconds = time_of_flight_sec + 0.15
        return elevation_correction_deg, fuze_delay_seconds

class Gerat58OilFeedingSystem:
    """Simulates the Rheinmetall mechanical pulse oiler."""
    def __init__(self):
        self.max_capacity_liters = 4.5
        self.current_oil_level_liters = 4.5
        self.oil_viscosity_nominal = True
        self.injection_nozzles_clear = True
        self.consumption_per_shot = 0.0015 

    def process_recoil_pulse(self, barrel_temp_celsius: float) -> dict:
        pulse_telemetry = {
            "oil_pumped": False,
            "lubrication_status": "CRITICAL_DRY",
            "oil_level_remaining_pct": 0.0
        }

        if not self.injection_nozzles_clear:
            pulse_telemetry["lubrication_status"] = "NOZZLE_CLOGGED"
            return pulse_telemetry

        if self.current_oil_level_liters <= 0.0:
            pulse_telemetry["lubrication_status"] = "RESERVOIR_EMPTY"
            return pulse_telemetry

        actual_consumption = self.consumption_per_shot
        if barrel_temp_celsius > 150.0:
            actual_consumption = actual_consumption * 1.5 

        self.current_oil_level_liters = max(0.0, self.current_oil_level_liters - actual_consumption)
        pulse_telemetry["oil_pumped"] = True
        pulse_telemetry["oil_level_remaining_pct"] = (self.current_oil_level_liters / self.max_capacity_liters) * 100.0
        
        if pulse_telemetry["oil_level_remaining_pct"] <= 15.0:
            pulse_telemetry["lubrication_status"] = "LOW_PRESSURE_WARNING"
            return pulse_telemetry

        pulse_telemetry["lubrication_status"] = "NOMINAL_FILM"
        return pulse_telemetry

class Gerat58StateEngine:
    """State machine managing the 17 interactive features, maintenance, and kinematics."""
    def __init__(self):
        self.current_mode = "TRANSPORT"
        self.pneumatic_pressure_bar = 0.0
        self.system_voltage = 0.0
        self.barrel_temperature_celsius = 20.0
        
        self.hardware_sensors = {
            "breech_block": "DOWN_OPEN",
            "compressed_air_charged": False,
            "extractor_claws_tripped": False
        }
        
        self.oiler = Gerat58OilFeedingSystem()
        
        self.controls: Dict[str, Any] = {
            "1_trigger_pedal": False,
            "2_safety_selector": "SICHER",
            "3_pneumatic_charging_lever": False,
            "4_breech_lock_handle": "LOCKED",
            "5_azimuth_handwheel_gear": "LOW",
            "6_elevation_handwheel_gear": "LOW",
            "7_main_power_switch": False,
            "8_servo_engagement_clutch": False,
            "9_radar_data_link": "LOCAL",
            "10_fuze_setter_inductor": 0.0,
            "11_gas_regulator_valve": 3.0,
            "12_recoil_buffer_valve": "CLOSED",
            "13_travel_lock_clamp": True,
            "14_outrigger_jacks": "RETRACTED",
            "15_spirit_levels_calibrated": False,
            "16_sight_illuminator_knob": 0.0,
            "17_intercom_link": "CONNECTED"
        }

    def change_system_mode(self, new_mode: str) -> str:
        allowed_modes = ["TRANSPORT", "COMBAT", "MAINTENANCE"]
        if new_mode not in allowed_modes:
            return "Invalid mode. Choose from: TRANSPORT, COMBAT, MAINTENANCE"
            
        if new_mode == "COMBAT":
            return self.setup_combat_mode()
            
        if new_mode == "MAINTENANCE":
            return self.setup_maintenance_mode()
            
        self.current_mode = "TRANSPORT"
        return "System Architecture Switched To: [TRANSPORT MODE]"

    def setup_combat_mode(self) -> str:
        """Guard-clause extraction for combat mode deployment."""
        if self.controls["13_travel_lock_clamp"]:
            return "CANNOT ENTER COMBAT MODE: Travel Lock Clamp is still engaged!"
        if self.controls["14_outrigger_jacks"] != "DEPLOYED":
            return "CANNOT ENTER COMBAT MODE: Outrigger Support Jacks are unextended!"
            
        self.system_voltage = 110.0
        self.controls["7_main_power_switch"] = True
        self.current_mode = "COMBAT"
        return "System Architecture Switched To: [COMBAT MODE]"

    def setup_maintenance_mode(self) -> str:
        """Guard-clause extraction for maintenance mode transition."""
        self.system_voltage = 0.0
        self.controls["8_servo_engagement_clutch"] = False
        self.controls["1_trigger_pedal"] = False
        self.current_mode = "MAINTENANCE"
        return "System Architecture Switched To: [MAINTENANCE MODE]"

    def actuate_control(self, feature_name: str, value: Any) -> str:
        if feature_name not in self.controls:
            return "Feature not recognized."
        
        if feature_name == "3_pneumatic_charging_lever" and value is True:
            self.pneumatic_pressure_bar = max(0.0, self.pneumatic_pressure_bar - 5.0)
            self.hardware_sensors["compressed_air_charged"] = True
            return "Feature 3 Actuated: High-pressure air accumulator flask primed."
            
        self.controls[feature_name] = value
        return f"Control Modified: {feature_name} set to {value}"

    def execute_loading_cycle(self) -> Tuple[bool, str]:
        """Runs the step-by-step pneumatic loading sequence."""
        if self.hardware_sensors["breech_block"] != "DOWN_OPEN":
            return False, "RAMMING BLOCKED: Breech wedge must be fully down and open."
            
        if not self.hardware_sensors["compressed_air_charged"]:
            return False, "PNEUMATIC FAILURE: Accumulator flask pressure too low."
            
        self.hardware_sensors["extractor_claws_tripped"] = True
        self.hardware_sensors["breech_block"] = "UP_CLOSED"
        return True, "Breech loaded, wedge locked home, firing pin cocked."

    def process_firing_sequence(self, cam: MechanicalBallisticCam, range_m: float, elevation_deg: float) -> Dict[str, Any]:
        """Evaluates safety checks, processes cam logic, calculates physics, and checks oil."""
        if self.current_mode != "COMBAT":
            return {"firing_status": "ABORTED", "reason": "Weapon is not in COMBAT mode."}
            
        if self.controls["2_safety_selector"] == "SICHER":
            return {"firing_status": "ABORTED", "reason": "Safety selector lever is set to SICHER."}

        load_success, load_msg = self.execute_loading_cycle()
        if not load_success:
            return {"firing_status": "ABORTED", "reason": load_msg}

        lead_correction, fuze_time = cam.read_cam_geometry(range_m, elevation_deg)
        self.controls["10_fuze_setter_inductor"] = fuze_time
        
        force_profile = calculate_ballistic_force(mass_kg=cam.projectile_mass_kg, velocity_m_s=cam.muzzle_velocity_m_s)
        
        self.hardware_sensors["breech_block"] = "DOWN_OPEN"
        self.hardware_sensors["extractor_claws_tripped"] = False
        self.barrel_temperature_celsius += 14.5
        
        oil_status = self.oiler.process_recoil_pulse(self.barrel_temperature_celsius)
        if oil_status['lubrication_status'] in ['RESERVOIR_EMPTY', 'NOZZLE_CLOGGED']:
            self.setup_maintenance_mode()
            return {"firing_status": "CRITICAL FAILURE", "reason": "Breech Friction Overload. Mode forced to MAINTENANCE."}
        
        return {
            "firing_status": "SUCCESSFUL 55mm DISCHARGE",
            "calculated_lead_deg": lead_correction,
            "inducted_fuze_time_sec": fuze_time,
            "recoil_force_kn": force_profile["force_kn"],
            "oil_pumped": oil_status["oil_pumped"],
            "oil_level_pct": oil_status["oil_level_remaining_pct"]
        }

def perform_oil_system_maintenance(state_engine: Gerat58StateEngine) -> bool:
    """Steps the visitor through bleeding the system and refilling the 4.5L oil reservoir."""
    print("LUFTWAFFE FLAK WERKSTATT - OIL RESERVOIR REFRESH PROTOCOL")
    
    if state_engine.current_mode != "MAINTENANCE":
        print("MAINTENANCE ABORTED! CRITICAL SAFETY RISK: Cannot open high-pressure lines outside of MAINTENANCE mode.")
        return False
        
    print("Condition Verified: Weapon safely isolated from servo power.")
    time.sleep(0.5)

    print("[STEP 1/4] Isolating electrical systems...")
    state_engine.actuate_control("7_main_power_switch", False)
    print("Feature 7: Main Power Switch flipped to OFF.")
    time.sleep(0.5)

    print("[STEP 2/4] Purging residual pneumatic and fluid pressures...")
    state_engine.actuate_control("12_recoil_buffer_valve", "OPEN")
    state_engine.oiler.current_oil_level_liters = 0.0
    print("System lines blown out.")
    time.sleep(0.5)

    print("[STEP 3/4] Clearing injection nozzle ports...")
    state_engine.oiler.injection_nozzles_clear = True
    print("Injection nozzles blown clear with dry air back-pressure.")
    time.sleep(0.5)

    print("[STEP 4/4] Pumping new hydraulic lubricant into reservoir...")
    state_engine.oiler.current_oil_level_liters = state_engine.oiler.max_capacity_liters
    state_engine.oiler.oil_viscosity_nominal = True
    print("Fluid replaced.")
    
    print("[COMPLETING TASK] Securing structural access hatches...")
    state_engine.actuate_control("12_recoil_buffer_valve", "CLOSED")
    print("MAINTENANCE SUCCESSFUL: Lubrication Subsystem Remanufactured!")
    return True

def run_museum_interactive_demo():
    print("RHEINMETALL GERAT 58 ANTI-AIRCRAFT SYSTEM INTERACTIVE ENGINE")
    
    gun = Gerat58StateEngine()
    ballistic_cam = MechanicalBallisticCam()
    
    gun.oiler.current_oil_level_liters = 0.002
    
    print("DEPLOYING WEAPON SYSTEM")
    print(gun.actuate_control("13_travel_lock_clamp", False))
    print(gun.actuate_control("14_outrigger_jacks", "DEPLOYED"))
    print(gun.change_system_mode("COMBAT"))
    print(gun.actuate_control("3_pneumatic_charging_lever", True))
    
    print("EXECUTING COMBAT FIRING LOOP")
    print("[Trigger Depressed] Firing Round 1...")
    report1 = gun.process_firing_sequence(ballistic_cam, 5000.0, 30.0)
    print(f"Status: {report1['firing_status']}")
    
    gun.actuate_control("3_pneumatic_charging_lever", True)
    
    print("[Trigger Depressed] Firing Round 2...")
    report2 = gun.process_firing_sequence(ballistic_cam, 4800.0, 32.0)
    print(f"Status: {report2['firing_status']}")
    print(f"Reason: {report2.get('reason', 'None')}")
    
    print("VISITOR MAINTENANCE INTERVENTION REQUIRED")
    perform_oil_system_maintenance(gun)

if __name__ == "__main__":
    run_museum_interactive_demo()
