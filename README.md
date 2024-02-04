# Mission-Control-Software

This repository contains all required software for the Mission control used in RTU HPR Team.

The Mission control consists of 3 main parts:
* Python processing software:
  * Receives and sends CCSDS packets between the transceivers and Yamcs. 
  * Does additional processing to get information from essential data packets.
  * Data from essential data packets is used to:
    * Calculate the required angles for the Antenna rotator system.
    * Calculate additional information from location data (Speed, distance, etc.).
  * Saves all outgoing data to log files.
* Yamcs mission control:
  * Save and view all received and sent packets.
  * Send commands to all other systems.
  * Interface for OpenMCT integration.
* OpenMCT dashboard:
  * Used to display and analyze all received data

## Usage

### Prerequsites
To use the basic functionality of the software, that Python processing software provides, only Python version 3.12 or higher is required.
If this Python version is not already installed on your system, you can download it from the official Python website:
* [Download Python](https://www.python.org/downloads/release/python-3120/)

To be able to use Yamcs mission control and OpenMCT dashboard Java JDK 11 and Node.js (MUST be version v19.9.0) is required.
* [Download Java JDK 11](https://www.oracle.com/java/technologies/javase/jdk11-archive-downloads.html)
* [Download Node.js v19.9.0](https://nodejs.org/download/release/v19.9.0/)

### Running Mission Control
To run just the Python processing software, run the `run_python_only.ps1` script. This script will open the Python virtual enviroment, install all required libraries and start the software.

To run the full version of the Mission control, run the `run_all.ps1` script. This script will do the same as above, in addition it will start the Yamcs and OpenMCT servers, and open the web interfaces for both servers.