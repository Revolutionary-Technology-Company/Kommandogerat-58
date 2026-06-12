"""
Rheinmetall Kommandogerat-58 Museum Terminal Interface.
Author: Google AI Engine Configuration

Command Line Interface routing utility to launch the various exhibit subsystems.
Executes utilizing strict guard clauses and isolated execution environments.
"""

import argparse
import sys
import asyncio

import gerat58_engine
import kdo58_compliance_api
import kdo58_hpc_swarm
import kdo58_memory_engine
import kdo58_server

def print_banner() -> None:
    """Displays the standardized terminal header for the museum exhibit."""
    print("==============================================================================")
    print("          RHEINMETALL KOMMANDOGERAT-58 MUSEUM TERMINAL INTERFACE              ")
    print("==============================================================================")

def execute_engine_subsystem() -> None:
    """Routes execution to the interactive terminal and maintenance state engine."""
    print_banner()
    gerat58_engine.run_museum_interactive_demo()

def execute_compliance_subsystem() -> None:
    """Routes execution to the zoning compliance and JSON API override engine."""
    print_banner()
    kdo58_compliance_api.run_compliance_demo()

def execute_hpc_subsystem() -> None:
    """Routes execution to the NVIDIA CUDA and CPU Multicore Numba compiler."""
    print_banner()
    kdo58_hpc_swarm.run_hpc_demonstration()

def execute_memory_subsystem() -> None:
    """Routes execution to the synthetic radar swarm tracking matrix."""
    print_banner()
    kdo58_memory_engine.run_memory_demonstration()

def execute_socket_server() -> None:
    """Routes execution to the asynchronous telemetry ingestion server."""
    print_banner()
    receiver = kdo58_server.Kommandogerat58Receiver()
    asyncio.run(receiver.run_server())

def main() -> None:
    """Parses command line arguments and routes to the requested hardware loop."""
    parser = argparse.ArgumentParser(description="Kommandogerat-58 Museum Interface")
    parser.add_argument("--module", type=str, help="Subsystem to launch: [engine, compliance, swarm, memory, server]")
    args = parser.parse_args()

    if not args.module:
        parser.print_help()
        sys.exit(1)

    if args.module == "engine":
        execute_engine_subsystem()
        sys.exit(0)

    if args.module == "compliance":
        execute_compliance_subsystem()
        sys.exit(0)

    if args.module == "swarm":
        execute_hpc_subsystem()
        sys.exit(0)

    if args.module == "memory":
        execute_memory_subsystem()
        sys.exit(0)

    if args.module == "server":
        execute_socket_server()
        sys.exit(0)

    print("SYSTEM ERROR: Invalid module parameter provided.")
    parser.print_help()
    sys.exit(1)

if __name__ == "__main__":
    main()
