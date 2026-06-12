import asyncio
import json
import math
import time
from typing import Dict, Tuple
import nidaqmx

def read_kabelverteiler():
    with nidaqmx.Task() as task:
        # Add all 16 channels from slot 1
        task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai0:15")
        data = task.read()
        return data
class Kommandogerat58Receiver:
    def __init__(self, host: str = "0.0.0.0", port: int = 1958):
        self.host = host
        self.port = port
        self.running = False
        
        # Internal state buffer representing decoded tracking telemetry
        self.telemetry_state = {
            "timestamp": 0.0,
            "radar_inputs": {"azimuth": 0.0, "elevation": 0.0, "range": 0.0},
            "gun_commands": {"azimuth": 0.0, "elevation": 0.0, "fuse_setting": 0.0},
            "battery_status": {"ready_interlock": False, "fire_command": False}
        }

    def decode_selsyn_pair(self, coarse_deg: float, fine_deg: float, gear_ratio: float = 36.0) -> float:
        """
        Reconstructs high-precision angles from the historical multi-speed transmission lines.
        Cables combined a 1:1 Coarse line with a 1:36 Fine precision line to avoid data slippage.
        """
        # Estimate coarse sector block
        coarse_sector = math.floor(coarse_deg / (360.0 / gear_ratio))
        # Reconstruct the absolute target position
        true_angle = (coarse_sector * (360.0 / gear_ratio)) + (fine_deg / gear_ratio)
        return true_angle % 360.0

    def parse_kabelverteiler_stream(self, raw_frame: bytes) -> Dict:
        """
        Simulates parsing a 64-byte structural frame reading from the 16 main lines via ADC hardware.
        """
        if len(raw_frame) < 64:
            return {}

        # Unpack raw analog-to-digital mappings from the Kabelverteiler pins
        # (Assuming structured float arrays mapping to specific cable banks)
        import struct
        unpacked_data = struct.unpack("!16f", raw_frame)
        
        # Mapping incoming channels corresponding to distribution topology
        c1_raw_az, c2_raw_el, c3_raw_rng = unpacked_data[0:3]
        c4_gun_az_c, c5_gun_az_f, c8_gun_el_c, c9_gun_el_f = unpacked_data[3:7]
        c12_fuse_time = unpacked_data[11]
        c15_control_bit = unpacked_data[14]

        # Resolution calculations
        true_gun_az = self.decode_selsyn_pair(c4_gun_az_c, c5_gun_az_f, gear_ratio=36.0)
        true_gun_el = self.decode_selsyn_pair(c8_gun_el_c, c9_gun_el_f, gear_ratio=36.0)

        return {
            "timestamp": time.time(),
            "radar_inputs": {
                "azimuth": round(c1_raw_az, 4),
                "elevation": round(c2_raw_el, 4),
                "range": round(c3_raw_rng, 2)
            },
            "gun_commands": {
                "azimuth": round(true_gun_az, 4),
                "elevation": round(true_gun_el, 4),
                "fuse_setting": round(c12_fuse_time, 3)
            },
            "battery_status": {
                "ready_interlock": bool(int(c15_control_bit) & 0x01),
                "fire_command": bool(int(c15_control_bit) & 0x02)
            }
        }

    async def handle_transmission_cable(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Manages the persistent TCP/Serial stream mimicking the physical Übertragungskabel socket connection.
        """
        peer = writer.get_extra_info('peername')
        print(f"[*] Physical Übertragungskabel interface locked onto: {peer}")

        try:
            while self.running:
                # Read structural frame blocks (64-bytes containing data from all lines)
                data = await reader.readexactly(64)
                if not data:
                    break
                
                parsed_state = self.parse_kabelverteiler_stream(data)
                if parsed_state:
                    self.telemetry_state = parsed_state
                    # Output data visually in standard JSON format for web dashboards / UI apps
                    print(json.dumps(self.telemetry_state, indent=2))
                    
                    # Echo back handshake acknowledgement via Cable Line 16 Sync
                    writer.write(b'\x01\x37\xFF\x00') 
                    await writer.drain()

        except asyncio.IncompleteReadError:
            print("[!] Stream truncated or Übertragungskabel physical disconnect.")
        except Exception as e:
            print(f"[!] Error processing line matrix: {e}")
        finally:
            print(f"[-] Dropping connection from: {peer}")
            writer.close()
            await writer.wait_closed()

    async def run_server(self):
        self.running = True
        server = await asyncio.start_server(self.handle_transmission_cable, self.host, self.port)
        print(f"[*] Kdo-G58 Computer listening on {self.host}:{self.port}...")
        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    receiver = Kommandogerat58Receiver()
    try:
        asyncio.run(receiver.run_server())
    except KeyboardInterrupt:
        print("\n[*] Shutting down fire control interface application.")
