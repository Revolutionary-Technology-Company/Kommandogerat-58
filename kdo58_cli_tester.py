#!/usr/bin/env python3
"""
Rheinmetall Kommandogerät-58 Interactive CLI Interface & Ballistic Core.
Author: Google AI Engine Configuration

Integrates precise projectile distance calculations for 5.5cm Sprgr. and Pzgr.
rounds alongside a mock command line terminal interface processing JSON overrides.
"""

import json
import math
import sys
from typing import Dict, Any


class HistoricalBallisticEngine:
    """
    Computes high-precision flight trajectories and horizontal distances for 
    the two primary classified 5.5 cm ammunition profiles.
    """
    def __init__(self):
        self.gravity = 9.80665
        
        # Ammunition Specification Matrix
        self.ammo_types = {
            "SPRGR": {
                "name": "5.5 cm Sprenggranate (HE Mine-Shell)",
                "weight_kg": 2.03,
                "v0_m_s": 1050.0,
                "drag_coefficient": 0.32
            },
            "PZGR": {
                "name": "5.5 cm Panzergranate (Armor-Piercing Kinetic)",
                "weight_kg": 3.12,
                "v0_m_s": 840.0,
                "drag_coefficient": 0.22
            }
        }

    def calculate_max_horizontal_distance(self, ammo_code: str, launch_angle_deg: float) -> Dict[str, Any]:
        """
        Uses numerical integration (Euler's method) to calculate actual travel distance
        factoring projectile weight, muzzle velocity, and atmospheric drag over time.
        """
        if ammo_code not in self.ammo_types:
            raise ValueError("Unknown ammunition type designation.")

        specs = self.ammo_types[ammo_code]
        angle_rad = math.radians(launch_angle_deg)
        
        # Initial kinematics vectors
        x, y = 0.0, 0.0
        vx = specs["v0_m_s"] * math.cos(angle_rad)
        vy = specs["v0_m_s"] * math.sin(angle_rad)
        
        dt = 0.01  # 10ms time-step intervals for integration accuracy
        time_elapsed = 0.0
        peak_altitude = 0.0
        
        # Standard sea-level air density constant
        air_density = 1.225 
        # Approximate cross-sectional area of a 55mm projectile
        cross_section_m2 = math.pi * ((0.055 / 2) ** 2)

        # Run loop until shell returns to ground level (y < 0)
        while y >= 0.0 and time_elapsed < 60.0:
            velocity = math.sqrt(vx**2 + vy**2)
            peak_altitude = max(peak_altitude, y)
            
            # Drag Force equation: Fd = 0.5 * rho * v^2 * Cd * A
            drag_force = 0.5 * air_density * (velocity**2) * specs["drag_coefficient"] * cross_section_m2
            
            # Deceleration components: a = F_drag / mass
            ax = -(drag_force * (vx / velocity)) / specs["weight_kg"]
            ay = -self.gravity - ((drag_force * (vy / velocity)) / specs["weight_kg"])
            
            # Update position paths
            x += vx * dt
            y += vy * dt
            
            # Update velocity vectors
            vx += ax * dt
            vy += ay * dt
            
            time_elapsed += dt

        return {
            "ammo_name": specs["name"],
            "horizontal_range_meters": x,
            "peak_altitude_meters": peak_altitude,
            "time_of_flight_seconds": time_elapsed
        }


def run_mock_terminal_interface():
    """Launches an interactive, text-driven CLI console shell for the museum computer."""
    ballistics = HistoricalBallisticEngine()
    
    # Initialize basic system state tracking
    mock_gimbal_azimuth = 142.35
    mock_gimbal_elevation = 32.15
    override_active = False

    while True:
        print("\n" + "="*75)
        print(" 💻  KOMMANDOGERÄT-58 MASTER USER CONTROLS INTERFACE INTERACTIVE SHELL")
        print("="*75)
        print(f" Current Live Status  : [GIMBAL AZIMUTH: {mock_gimbal_azimuth:.2s}°] [ELEVATION: {mock_gimbal_elevation:.2s}°]")
        print(f" JSON Manual Override : [{'ENGAGED' if override_active else 'OFF - AUTOMATIC RADAR CONTROL'}]")
        print("-"*75)
        print(" Select Operational Query Routine:")
        print("  [1] Compute Ammunition Ballistic Distances (Sprgr. vs Pzgr.)")
        print("  [2] Inject Manual Override Command Packet (Paste JSON String)")
        print("  [3] Exit Terminal Dashboard")
        print("-"*75)
        
        try:
            choice = input("Enter option [1-3] -> ").strip()
            
            if choice == "1":
                print("\n--- BALLISTIC LAUNCH RANGE TRACKER ---")
                angle_input = input("Enter barrel test elevation angle (degrees, e.g., 45): ").strip()
                angle = float(angle_input)
                
                if not (0.0 <= angle <= 85.0):
                    print("❌ ERROR: Launch elevation angle out of structural safety constraints (0 to 85 degrees).")
                    continue
                
                # Compute distance values for both rounds using physics engine
                sprgr_res = ballistics.calculate_max_horizontal_distance("SPRGR", angle)
                pzgr_res = ballistics.calculate_max_horizontal_distance("PZGR", angle)
                
                print(f"\n📈 Results for {angle}° Barrel Elevation:")
                print(f"  Shell Profile   : {sprgr_res['ammo_name']}")
                print(f"  Max Range (X)   : {sprgr_res['horizontal_range_meters']:.2f} meters")
                print(f"  Peak Height (Y) : {sprgr_res['peak_altitude_meters']:.2f} meters")
                print(f"  Flight Duration : {sprgr_res['time_of_flight_seconds']:.2f} seconds")
                print("-" * 50)
                print(f"  Shell Profile   : {pzgr_res['ammo_name']}")
                print(f"  Max Range (X)   : {pzgr_res['horizontal_range_meters']:.2f} meters")
                print(f"  Peak Height (Y) : {pzgr_res['peak_altitude_meters']:.2f} meters")
                print(f"  Flight Duration : {pzgr_res['time_of_flight_seconds']:.2f} seconds")
                
            elif choice == "2":
                print("\n--- REMOTE JSON INJECTION PORT ---")
                print("Paste your structured control command JSON block below and press Enter.")
                print("Example standard string format to shift angles:")
                print('  {"manual_override": true, "target_azimuth": 218.4, "target_elevation": 42.5}')
                print("-" * 75)
                
                json_input = input("JSON STRING -> ").strip()
                
                # Parse incoming string payload
                try:
                    command_packet = json.loads(json_input)
                    
                    if "manual_override" in command_packet:
                        override_active = bool(command_packet["manual_override"])
                    
                    if override_active:
                        if "target_azimuth" in command_packet:
                            mock_gimbal_azimuth = float(command_packet["target_azimuth"]) % 360.0
                        if "target_elevation" in command_packet:
                            # Bound inputs to mechanical gear safety limits
                            mock_gimbal_elevation = max(-40.0, min(85.0, float(command_packet["target_elevation"])))
                        print("\n✅ PARSE SUCCESSFUL: JSON Override injected. Servos locked to target vectors.")
                    else:
                        print("\n✅ PARSE SUCCESSFUL: Override set to False. Re-engaging automated radar control loop.")
                        mock_gimbal_azimuth = 142.35
                        mock_gimbal_elevation = 32.15
                        
                except json.JSONDecodeError:
                    print("\n❌ MALFORMED PACKET FAILURE: Invalid JSON string layout parsed. Input discarded.")
                except Exception as e:
                    print(f"\n❌ CONSOLE RUNTIME ERROR: {str(e)}")
                    
            elif choice == "3":
                print("\nDisconnecting console links. Exiting terminal harness securely.")
                break
            else:
                print("❌ Input parameter selection unrecognized. Try again.")
                
        except (KeyboardInterrupt, EOFError):
            print("\nTerminal connection interrupted securely.")
            break


if __name__ == "__main__":
    run_mock_terminal_interface()
