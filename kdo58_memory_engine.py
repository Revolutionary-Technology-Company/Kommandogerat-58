"""
Rheinmetall Kommandogerat-58 Target Memory Engine.
Author: Google AI Engine Configuration
Maintains a deterministic state matrix of active aerial tracks for the HPC swarm processor.
"""

import time
import numpy as np
from typing import Dict, Any, List

class TargetTrack:
    """Represents a single deterministic radar track."""
    
    def __init__(self, track_id: str, range_m: float, elevation_deg: float, azimuth_deg: float):
        self.track_id = track_id
        self.range_m = range_m
        self.elevation_deg = elevation_deg
        self.azimuth_deg = azimuth_deg
        self.status = "ACTIVE"
        self.last_update_time = time.time()

class SwarmMemoryEngine:
    """Manages the lifecycle, pruning, and state compilation of all radar contacts."""
    
    def __init__(self):
        self.active_tracks: Dict[str, TargetTrack] = {}
        self.max_tracking_range_meters = 15000.0
        self.min_tracking_range_meters = 500.0

    def register_target(self, track_id: str, range_m: float, el_deg: float, az_deg: float) -> str:
        """Injects a new radar track into the memory matrix."""
        if track_id in self.active_tracks:
            return "TRACK REGISTRATION FAILED: Track ID already exists."

        if range_m > self.max_tracking_range_meters:
            return "TRACK REGISTRATION FAILED: Target exceeds maximum acquisition range."

        self.active_tracks[track_id] = TargetTrack(track_id, range_m, el_deg, az_deg)
        return "TRACK REGISTRATION SUCCESSFUL"

    def update_target_kinematics(self, track_id: str, delta_range: float, delta_el: float, delta_az: float) -> str:
        """Updates the spatial coordinates of an existing track during a clock tick."""
        if track_id not in self.active_tracks:
            return "UPDATE FAILED: Track ID not found."

        track = self.active_tracks[track_id]
        track.range_m = track.range_m + delta_range
        track.elevation_deg = track.elevation_deg + delta_el
        track.azimuth_deg = track.azimuth_deg + delta_az
        track.last_update_time = time.time()

        if track.range_m < self.min_tracking_range_meters:
            track.status = "BLIND_ZONE_DROPPED"
            return "UPDATE SUCCESSFUL: Target entered blind zone. Status modified."

        return "UPDATE SUCCESSFUL: Kinematics adjusted."

    def flag_target_destroyed(self, track_id: str) -> str:
        """Marks a track as neutralized by the firing loop."""
        if track_id not in self.active_tracks:
            return "FLAG FAILED: Track ID not found."

        self.active_tracks[track_id].status = "DESTROYED"
        return "FLAG SUCCESSFUL: Target neutralized."

    def purge_stale_and_destroyed_tracks(self) -> int:
        """Removes inactive or destroyed tracks from the memory matrix to free heap space."""
        keys_to_remove: List[str] = []
        current_time = time.time()

        for track_id, track in self.active_tracks.items():
            if track.status == "DESTROYED":
                keys_to_remove.append(track_id)
                continue

            if track.status == "BLIND_ZONE_DROPPED":
                keys_to_remove.append(track_id)
                continue

            if (current_time - track.last_update_time) > 10.0:
                keys_to_remove.append(track_id)

        for key in keys_to_remove:
            del self.active_tracks[key]

        return len(keys_to_remove)

    def export_hpc_arrays(self) -> Dict[str, np.ndarray]:
        """Compiles the object memory into contiguous Numpy arrays for the Numba and CUDA kernels."""
        active_count = 0
        for track in self.active_tracks.values():
            if track.status == "ACTIVE":
                active_count = active_count + 1

        ranges = np.zeros(active_count, dtype=np.float64)
        elevations = np.zeros(active_count, dtype=np.float64)
        azimuths = np.zeros(active_count, dtype=np.float64)

        index = 0
        for track in self.active_tracks.values():
            if track.status == "ACTIVE":
                ranges[index] = track.range_m
                elevations[index] = track.elevation_deg
                azimuths[index] = track.azimuth_deg
                index = index + 1

        return {
            "ranges": ranges,
            "elevations": elevations,
            "azimuths": azimuths
        }

def run_memory_demonstration():
    """Validates the memory engine and array export sequence."""
    print("RHEINMETALL KOMMANDOGERAT-58 TARGET MEMORY ENGINE")
    
    memory = SwarmMemoryEngine()
    
    print("Registering incoming swarm...")
    print(memory.register_target("ALPHA_01", 8000.0, 45.0, 120.0))
    print(memory.register_target("BRAVO_02", 7500.0, 42.0, 125.0))
    print(memory.register_target("CHARLIE_03", 400.0, 10.0, 90.0))
    
    print("Processing kinematic updates...")
    print(memory.update_target_kinematics("ALPHA_01", -500.0, -1.0, 0.0))
    print(memory.flag_target_destroyed("BRAVO_02"))
    
    print("Purging stale and destroyed contacts...")
    purged_count = memory.purge_stale_and_destroyed_tracks()
    print(f"Removed {purged_count} dead tracks from memory.")
    
    print("Exporting matrices to High Performance Computing core...")
    hpc_payload = memory.export_hpc_arrays()
    
    print("Contiguous Memory Blocks Generated:")
    print(f"Ranges Array     : {hpc_payload['ranges']}")
    print(f"Elevations Array : {hpc_payload['elevations']}")

if __name__ == "__main__":
    run_memory_demonstration()
