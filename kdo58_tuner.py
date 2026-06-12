import math

class BarrelHarmonicStrutTuner:
    """
    Simulates a mechanical barrel harmonic tuner strut (Resonanzmuffe).
    Adjusts length to match the acoustic resonant frequencies of 55mm ammunition.
    """
    def __init__(self):
        self.base_barrel_length_m = 4.2
        self.speed_of_sound_steel_m_s = 5050.0
        self.rifling_twist_rate_m = 1.65 # Distance for one full rotation

    def calculate_tuning_profile(self, ammo_type: str) -> dict:
        """
        Computes the target strut length to match wave energy node baselines.
        Accepted types: 'SPRGR' (HE Shell) or 'PZGR' (AP Shell)
        """
        if ammo_type == "SPRGR":
            v0 = 1050.0
            label = "5.5 cm Sprenggranate (HE Mine)"
        elif ammo_type == "PZGR":
            v0 = 840.0
            label = "5.5 cm Panzergranate (AP Kinetic)"
        else:
            return {"error": "Ammunition type profile unrecognized"}

        # 1. Calculate natural rotational vibration frequency (f = velocity / twist)
        resonant_frequency_hz = v0 / self.rifling_twist_rate_m
        
        # 2. Compute structural acoustic wavelength (lambda = v_steel / f)
        wavelength_m = self.speed_of_sound_steel_m_s / resonant_frequency_hz
        quarter_wave_node = wavelength_m / 4.0
        
        # 3. Find the multiple that extends past the base barrel length
        node_multiple = 1
        while (quarter_wave_node * node_multiple) < self.base_barrel_length_m:
            node_multiple += 1
            
        target_total_length = quarter_wave_node * node_multiple
        required_strut_extension = target_total_length - self.base_barrel_length_m

        return {
            "ammo_profile": label,
            "vibration_frequency_hz": resonant_frequency_hz,
            "acoustic_wavelength_m": wavelength_m,
            "optimum_total_length_m": target_total_length,
            "required_strut_extension_m": required_strut_extension,
            "energy_efficiency_pct": 100.0  # Theoretical maximum destructive interference node
        }

# --- Quick Console Verification Test ---
if __name__ == "__main__":
    tuner = BarrelHarmonicStrutTuner()
    
    for round_code in ["SPRGR", "PZGR"]:
        profile = tuner.calculate_tuning_profile(round_code)
        print(f"=== HARMONIC STRUT PROFILE FOR: {profile['ammo_profile']} ===")
        print(f"  Resonant Audio Note   : {profile['vibration_frequency_hz']:.2f} Hz")
        print(f"  Target Overall Length : {profile['optimum_total_length_m']:.3f} meters")
        print(f"  🔧 LENGTH TO EXTEND STRUT : {profile['required_strut_extension_m']:.3f} meters")
        print("-" * 65)
