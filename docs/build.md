# Hardware Build Guide: National Instruments Architecture

## Overview
This document outlines the hardware architecture required to interface the historical **Kommandogerät 58 (Kabelverteiler)** and the modern **Rheinmetall MSP 500** with the museum's digital display network. 

To ensure maximum reliability in an outdoor exhibit environment and to comply with domestic manufacturing requirements, this build utilizes a **National Instruments (NI) CompactDAQ (cDAQ)** system. This aerospace-grade, modular platform acts as a unified edge-controller, ingesting both the 16 legacy analog voltage lines and the modern RS-422 differential serial feed into a single Python environment.

---

## 1. Bill of Materials (BOM)

| Component | Function | Description / Notes |
| :--- | :--- | :--- |
| **NI cDAQ-9132** (or similar) | Embedded Controller | Rugged, fanless chassis running NI Linux Real-Time. Hosts the Python server natively. |
| **NI-9205** | Analog Input Module | 32-Channel (Single-Ended) / 16-Channel (Differential) analog input. Used to read the 16 analog voltages from the WWII Kabelverteiler. |
| **NI-9870** | Serial Output Module | 4-Port RS-422/RS-485 module. Used to ingest the digital telemetry stream from the Rheinmetall MSP 500. |
| **NI PS-15** | Power Supply | Industrial 24V DC DIN-rail power supply for the cDAQ chassis. |

---

## 2. Hardware Wiring Map

### A. The Legacy Array (Kabelverteiler to NI-9205)
The 16 historical transmission cables (*Übertragungskabel*) must be spliced or pinned into a standard 37-pin D-Sub connector to interface with the NI-9205 module.

* **C1 - C3 (Radar Inputs):** Map to AI0 - AI2
* **C4 - C7 (Gun Azimuth Coarse/Fine):** Map to AI3 - AI6
* **C8 - C11 (Gun Elevation Coarse/Fine):** Map to AI7 - AI10
* **C12 - C14 (Fuse Setters):** Map to AI11 - AI13
* **C15 (Interlock/Fire Command):** Map to AI14
* **C16 (Sync Reference):** Map to AI15

*Note: Ensure the grounding loop from the physical museum exhibit shares a common ground with the NI-9205 COM pin to prevent floating voltage errors on the Selsyn reads.*

### B. The Modern Array (Rheinmetall MSP 500 to NI-9870)
The MSP 500 utilizes a differential RS-422 protocol. Connect the ruggedized serial feed from the MSP 500 to **Port 1** of the NI-9870 module using an RJ50 to DB9 adapter (provided by NI).

**RS-422 Pinout (DB9):**
* Pin 8: RX+ 
* Pin 9: RX-
* Pin 4: TX+
* Pin 5: TX-
* Pin 1: GND

---

## 3. Software Environment Setup

The cDAQ controller runs a robust embedded Linux OS. You will SSH into the controller to set up the Python environment that runs `kdo58_server.py`.

### 3.1. Install Dependencies
Log into the cDAQ terminal as `admin`. The controller uses `opkg` (Open PacKage Management) and standard `pip`.

```bash
# Update package lists
opkg update

# Install Python 3 and PIP if not present in the base image
opkg install python3 python3-pip

# Install the hardware communication APIs
pip install nidaqmx pyserial
