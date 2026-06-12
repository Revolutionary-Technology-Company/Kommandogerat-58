# Kommandogerät 58 (Museum Digital Reconstruction)

## Overview

This repository contains the software architecture required to interface a digital targeting application with the historical **Gerät 58 (5.5 cm FlaK)** museum array.

Historically, the connection between the Kommandogerät 58 fire-control computer and the gun battery was managed by a central distributor box (*Kabelverteiler*) utilizing a 36-conductor (*36-Ader*) transmission cable (*Übertragungskabel*). This application modernizes that pipeline, reading simulated or physical radar data, decoding multi-speed Selsyn (Drehmelder) phases, and outputting clean digital telemetry to the museum's automated gun servos.

## System Architecture

The pipeline consists of three main stages:

1. **Hardware Ingestion (ADC):** Analog signals from the 16 distributor cables are read via an Analog-to-Digital Converter (e.g., Arduino/Raspberry Pi).
2. **Telemetry Server (`kdo58_server.py`):** A Python-based asynchronous server that parses 64-byte structural frames.
3. **Targeting Output:** Clean JSON telemetry containing absolute tracking angles and battery interlock states.

## The 16-Cable Data Map

To safely reconstruct the data flow, the 16 physical connections are explicitly mapped into specific functional groups.

**Sensor Input Channels (Radar to Computer)**

* 
**C1 - C3:** Raw Radar/Optical Target Azimuth ($\alpha$), Elevation ($\epsilon$), and Slant Range ($D$).



**Command Outputs (Computer to Guns)**

* 
**C4 - C7:** Coarse and Fine Azimuth target tracking command angles ($\alpha_{gun}$) for Guns 1–4.


* 
**C8 - C11:** Coarse and Fine Elevation target tracking command angles ($\epsilon_{gun}$) for Guns 1–4.


* 
**C12 - C14:** Mechanical Fuse Setter Times ($\tau$) transmitted to the automatic barrel-load tray.



**Tactical and Synchronization Lines**

* 
**C15:** Command to Fire, Salvo Interrupts, and Battery Ready Interlocks.


* 
**C16:** 3-Phase AC Reference Voltage (typically 110V/400Hz) used to maintain angular synchronization across all Selsyns.



## Signal Processing Notes

To prevent data slippage during rapid target tracking, the analog system utilized a multi-speed Selsyn transmission. Our application recreates this by evaluating phase corrections between the 1:1 "Coarse" line and the 1:36 "Fine" precision line at sample frequencies exceeding 100 Hz. The Python server dynamically estimates the coarse sector block and mathematically reconstructs the absolute target angle.
