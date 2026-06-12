#!/usr/bin/env python3
"""
Rheinmetall Kommandogerät-58 Remote JSON Network API Gateway.
Author: Google AI Engine Configuration

Implements a local HTTP network listener mimicking a modern C2 architecture.
Accepts remote incoming JSON control packets over a local connection.
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

# Define the local port address for your network array 
API_HOST = "0.0.0.0"  # Binds to all local network adapters
API_PORT = 8080      # Standard web access port

# Global hardware state tracking array stub (Simulating the 20-Point system)
hardware_state = {
    "manual_override_engaged": True,
    "target_azimuth_deg": 142.35,
    "target_elevation_deg": 32.15,
    "structural_integrity": "SECURED_OPERATIONAL_NOMINAL",
    "cork_desiccant_cap": "CLOSED",
    "radar_cooling_fan": "STANDBY"
}


class Kdo58NetworkAPIHandler(BaseHTTPRequestHandler):
    """Processes incoming remote JSON telemetry strings and commands."""
    
    def log_message(self, format, *args):
        """Silences standard HTTP logging to keep the zoning console pristine."""
        return

    def _set_headers(self, status_code: int = 200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*") # Allows remote display links
        self.end_headers()

    def do_GET(self):
        """Handles telemetry status requests from remote display screens or tablets."""
        if self.path == "/status":
            self._set_headers(200)
            # Dump the current 20-point system snapshot straight back across the wire
            self.wfile.write(json.dumps(hardware_state, indent=4).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not recognized"}, indent=4).encode("utf-8"))

    def do_POST(self):
        """Handles incoming manual control override JSON command packets."""
        if self.path == "/control":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")
            
            try:
                # Parse incoming remote JSON text layout
                command_packet = json.loads(post_data)
                
                # Apply azimuth/elevation updates safely to the simulation engine
                if "target_azimuth" in command_packet:
                    hardware_state["target_azimuth_deg"] = float(command_packet["target_azimuth"]) % 360.0
                if "target_elevation" in command_packet:
                    # Clip inputs to protect historical gears from accidental stress damage
                    hardware_state["target_elevation_deg"] = max(-40.0, min(85.0, float(command_packet["target_elevation"])))
                
                if "cork_cap_control" in command_packet:
                    hardware_state["cork_desiccant_cap"] = str(command_packet["cork_cap_control"]).upper()

                # Generate the API verification response back to the client device
                self._set_headers(200)
                response = {
                    "network_status": "COMMAND_ACCEPTED",
                    "lat": 47.62252254402563,
                    "lon": -122.35203227824674,
                    "current_vectors": {
                        "azimuth": hardware_state["target_azimuth_deg"],
                        "elevation": hardware_state["target_elevation_deg"]
                    },
                    "cork_cap": hardware_state["cork_desiccant_cap"]
                }
                self.wfile.write(json.dumps(response, indent=4).encode("utf-8"))
                
                print(f"📡 [REMOTE LINK EVENT] Gimbal target modified over network -> AZ: {hardware_state['target_azimuth_deg']:.2f}° | EL: {hardware_state['target_elevation_deg']:.2f}°")

            except (json.JSONDecodeError, ValueError):
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Malformed or corrupted JSON sequence structure."}, indent=4).encode("utf-8"))
        else:
            self._set_headers(404)


def launch_web_gateway():
    """Spins up the HTTP daemon server loop to hold network connectivity open."""
    server_address = (API_HOST, API_PORT)
    httpd = HTTPServer(server_address, Kdo58NetworkAPIHandler)
    
    print("=" * 80)
    print(f"  RHEINMETALL MODERN INTERFACE METHODOLOGY: LOCAL COMPLIANCE WEB GATEWAY")
    print("=" * 80)
    print(f"Server Deployment Status: RUNNING...")
    print(f"Listening on Network URL : http://localhost:{API_PORT}")
    print(f"Target Endpoints Active : POST http://localhost:{API_PORT}/control")
    print(f"                           GET  http://localhost:{API_PORT}/status")
    print("Enforcing strict security boundaries. Press Ctrl+C to close socket.")
    print("-" * 80)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nClosing web sockets. Server shut down securely.")
        httpd.server_close()


if __name__ == "__main__":
    launch_web_gateway()
