# Ghost Map

Map the information from the lidar (which is on the drone) into a custom 3D mapping environment.

## How to run

The code is tested on ubuntu and raspberry pi OS (the given instructions are for linux)

### lidar

1. Make a python venv `python3 -m venv test_venv`
2. Source the venv `source test_venv/bin/activate`
3. Install the required packages `pip install numpy pandas pyopengl pygame rplidar-robotica adafruit-circuitpython-rplidar`
4. Run the lidar files with `python3 filename.py` (You need RPLidar A1M8 harware connected to you computer)

### hardware

1. You need to connect the hardware to the ESP32 (refer the schematic and the code which contains what to connect where)
2. Choose ESP32 Wroom DA module are the board in the Arduino IDE and the port based on the OS
3. Upload the code and use the serial monitor to look at the results (text)

### visualization

1. Make a python venv `python3 -m venv test_venv`
2. Source the venv `source test_venv/bin/activate`
3. Install the required packages `pip install pyopengl pygame pyopengl_accelerate numpy pandas`
4. Install one special package `pip install "imgui[pygame]"`
5. Run the viewer file with `python3 viewer.py`

## Stats for fun

- Crashes: 2
- Fatal Crashes: 1
- Current crash prevention strategy: Having Aman run under the drone to catch it (effective)

## Outputs

The outputs are shown in the video and the report
