from rplidar import RPLidar
import time

PORT_NAME = '/dev/ttyUSB0'
BAUD_RATE = 115200

def simple_test():
    lidar = RPLidar(PORT_NAME, BAUD_RATE)
    
    try:
        print(f"Connected to {PORT_NAME}")
        print("Getting health status...")
        info = lidar.get_info()
        print(f"Info: {info}")
        
        health = lidar.get_health()
        print(f"Health: {health}")
        
        print("\nStarting motor... (Look at the sensor, is it spinning?)")
        
        count = 0
        for scan in lidar.iter_scans():
            count += 1
            num_points = len(scan)
            
            if num_points > 0:
                first_point = scan[0]
                print(f"Scan #{count} | Points: {num_points} | First Point Data: {first_point}")
                print(f"   -> Angle: {first_point[1]:.2f}°, Dist: {first_point[2]:.2f}mm")
            else:
                print(f"Scan #{count} | Empty scan returned!")
            
            if count >= 10:
                break
                
    except Exception as e:
        print(f"\nERROR: {e}")
        
    finally:
        print("\nStopping...")
        lidar.stop()
        lidar.stop_motor()
        lidar.disconnect()

if __name__ == '__main__':
    simple_test()

