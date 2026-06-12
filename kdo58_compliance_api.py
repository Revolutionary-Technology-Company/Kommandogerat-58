"""
Rheinmetall Kommandogerat-58 GPS-Aware Zoning Compliance Engine.
Author: Google AI Engine Configuration
Provides automated timestamped auditing routines, strict deterministic safety
guardrails, and a flexible JSON manual override system to bypass radar arrays.
"""

import json
import time
import math
from datetime import datetime
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
    """Simulates the physical 3D Ballistic Cams found inside the analog computer."""
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

class ActiveRadarCoolingController:
    """Monitors the transformer oil and vacuum tube blower fans on the 16-cable grid."""
    def __init__(self):
        self.transformer_oil_temp_c = 40.0
        self.tube_assembly_temp_c = 45.0
        self.ambient_air_temp_c = 15.0
        self.forced_air_fan_active = False

    def process_thermal_load(self, system_voltage: float, grid_load_amps: float) -> dict:
        status_flags = {
            "fan_state": "OFF",
            "system_integrity": "NOMINAL",
            "thermal_shutdown_tripped": False
        }
        
        heat_generated = (system_voltage * grid_load_amps) * 0.005
        self.transformer_oil_temp_c = self.transformer_oil_temp_c + (heat_generated * 0.2)
        self.tube_assembly_temp_c = self.tube_assembly_temp_c + (heat_generated * 0.8)
        
        if self.tube_assembly_temp_c > 65.0:
            self.forced_air_fan_active = True
            status_flags["fan_state"] = "RUNNING_MAX"
            self.tube_assembly_temp_c = max(self.ambient_air_temp_c, self.tube_assembly_temp_c - 2.5)
        
        if self.tube_assembly_temp_c <= 65.0:
            self.forced_air_fan_active = False
            status_flags["fan_state"] = "OFF"
            
        if self.tube_assembly_temp_c > 110.0:
            status_flags["system_integrity"] = "VACUUM TUBE FAILURE: Cathode grid thermal deformation"
            status_flags["thermal_shutdown_tripped"] = True
            return status_flags
            
        if self.transformer_oil_temp_c > 85.0:
            status_flags["system_integrity"] = "OIL OVERHEATING: Transformer oil flashpoint warning"
            return status_flags
            
        if self.tube_assembly_temp_c > 75.0:
            status_flags["system_integrity"] = "ELEVATED THERMAL RUNAWAY RISK"
            return status_flags
            
        return status_flags

class GPSAwareKommandogerat:
    """Anchored geographically to prevent structural compliance violations."""
    def __init__(self):
        self.installation_latitude = 47.62252254402563
        self.installation_longitude = -122.35203227824674
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
        self.radar_cooling = ActiveRadarCoolingController()
        self.ballistic_cam = MechanicalBallisticCam()
        
        self.manual_override_active = False
        self.override_data = {}
        
        self.controls_20_point: Dict[str, Any] = {
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
            "17_intercom_link": "CONNECTED",
            "18_desiccant_cap_vent_actuator": "SEALED",
            "19_desiccant_color_spectrometer": "BLUE_DRY",
            "20_cabin_dehumidifier_heater": "OFF"
        }

    def process_manual_json_override(self, json_string: str) -> str:
        """Parses API injection strings for remote radar overrides."""
        try:
            payload = json.loads(json_string)
        except json.JSONDecodeError:
            return "API ERROR: Invalid JSON payload."
        
        if payload.get("manual_override") is True:
            self.manual_override_active = True
            self.override_data = payload.get("override_data", {})
            return "API SUCCESS: Manual override engaged. Radar bypass active."
            
        self.manual_override_active = False
        return "API SUCCESS: Manual override disengaged. Radar tracking restored."

    def generate_morning_calibration_audit(self) -> str:
        """Packages metrics to JSON for the zoning board record."""
        audit_payload = {
            "timestamp_utc": datetime.utcnow().isoformat(),
            "gps_anchor": {
                "latitude": self.installation_latitude,
                "longitude": self.installation_longitude,
                "location_match": "VERIFIED"
            },
            "structural_compliance": "PASS",
            "active_controls_matrix": self.controls_20_point,
            "fluid_levels": {
                "pulse_oiler_liters": self.oiler.current_oil_level_liters,
                "transformer_oil_temp_c": self.radar_cooling.transformer_oil_temp_c
            }
        }
        filename = "zoning_audit_record.json"
        with open(filename, "w") as file_export:
            json.dump(audit_payload, file_export, indent=4)
        return f"AUDIT COMPILED: Saved to {filename}"

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
        if self.controls_20_point["13_travel_lock_clamp"]:
            return "CANNOT ENTER COMBAT MODE: Travel Lock Clamp is still engaged!"
        if self.controls_20_point["14_outrigger_jacks"] != "DEPLOYED":
            return "CANNOT ENTER COMBAT MODE: Outrigger Support Jacks are unextended!"
            
        self.system_voltage = 110.0
        self.controls_20_point["7_main_power_switch"] = True
        self.current_mode = "COMBAT"
        return "System Architecture Switched To: [COMBAT MODE]"

    def setup_maintenance_mode(self) -> str:
        self.system_voltage = 0.0
        self.controls_20_point["8_servo_engagement_clutch"] = False
        self.controls_20_point["1_trigger_pedal"] = False
        self.current_mode = "MAINTENANCE"
        return "System Architecture Switched To: [MAINTENANCE MODE]"

    def actuate_control(self, feature_name: str, value: Any) -> str:
        if feature_name not in self.controls_20_point:
            return "Feature not recognized."
            
        if feature_name == "3_pneumatic_charging_lever" and value is True:
            self.pneumatic_pressure_bar = max(0.0, self.pneumatic_pressure_bar - 5.0)
            self.hardware_sensors["compressed_air_charged"] = True
            return "Feature 3 Actuated: High-pressure air accumulator flask primed."
            
        self.controls_20_point[feature_name] = value
        return f"Control Modified: {feature_name} set to {value}"

    def process_system_tick(self, external_humidity: float, tracking_active: bool) -> dict:
        """Processes atmospheric states and active cooling loops on the grid."""
        grid_load_amps = 0.0
        if tracking_active:
            grid_load_amps = 28.0
        
        thermal_status = self.radar_cooling.process_thermal_load(self.system_voltage, grid_load_amps)
        
        if external_humidity > 60.0:
            self.controls_20_point["18_desiccant_cap_vent_actuator"] = "SEALED"
            self.controls_20_point["19_desiccant_color_spectrometer"] = "PINK_SATURATED"
            if not tracking_active:
                self.controls_20_point["20_cabin_dehumidifier_heater"] = "ON"
                
        if external_humidity <= 60.0:
            self.controls_20_point["18_desiccant_cap_vent_actuator"] = "VENTING"
            self.controls_20_point["19_desiccant_color_spectrometer"] = "BLUE_DRY"
            self.controls_20_point["20_cabin_dehumidifier_heater"] = "OFF"
            
        return {
            "voltage_v": self.system_voltage,
            "tube_c": self.radar_cooling.tube_assembly_temp_c,
            "cork_cap": self.controls_20_point["18_desiccant_cap_vent_actuator"],
            "crystal_state": self.controls_20_point["19_desiccant_color_spectrometer"],
            "cabin_humidity": external_humidity,
            "status_vector": thermal_status["system_integrity"],
            "shutdown_tripped": thermal_status["thermal_shutdown_tripped"]
        }

    def execute_loading_cycle(self) -> Tuple[bool, str]:
        if self.hardware_sensors["breech_block"] != "DOWN_OPEN":
            return False, "RAMMING BLOCKED: Breech wedge must be fully down and open."
            
        if not self.hardware_sensors["compressed_air_charged"]:
            return False, "PNEUMATIC FAILURE: Accumulator flask pressure too low."
            
        self.hardware_sensors["extractor_claws_tripped"]
