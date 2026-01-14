import math
import time
import threading
import collections
import colorsys
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from adafruit_rplidar import RPLidar, RPLidarException

PORT_NAME = '/dev/ttyUSB0'
BAUD_RATE = 256000
MAX_DISTANCE_MM = 4000
WINDOW_SIZE = (1024, 768)
HISTORY_SIZE = 30

scan_history = collections.deque(maxlen=HISTORY_SIZE)
running = True

class LidarThread(threading.Thread):
    def run(self):
        global running
        print("Lidar Thread: Started.")

        while running:
            lidar = None
            try:
                lidar = RPLidar(None, PORT_NAME, baudrate=BAUD_RATE, timeout=3)
                
                lidar.stop()
                lidar.disconnect()
                time.sleep(0.5)
                lidar.connect()
                
                print(f"Lidar Health: {lidar.health}") 
                
                for scan in lidar.iter_scans():
                    if not running: break
                    
                    current_points = []
                    for (_, angle, distance) in scan:
                        if distance > 0:
                            rad = math.radians(angle)
                            x = distance * math.cos(rad)
                            y = distance * math.sin(rad)
                            current_points.append((x, y, distance))
                    
                    if current_points:
                        scan_history.append(current_points)

            except RPLidarException as e:
                print(f"Lidar Sync Error: {e} -> Resetting driver...")
                time.sleep(1.0)
                
            except Exception as e:
                print(f"Critical Lidar Error: {e}")
                time.sleep(2.0)
                
            finally:
                if lidar:
                    try:
                        lidar.stop()
                        lidar.disconnect()
                    except:
                        pass

def get_rainbow_color(distance, max_dist):
    """Returns an RGB color based on distance (Heatmap style)"""
    norm = min(distance, max_dist) / max_dist
    hue = (1.0 - norm) * 0.66 
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    return (r, g, b)

def init_opengl():
    glClearColor(0.05, 0.05, 0.1, 1.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-MAX_DISTANCE_MM, MAX_DISTANCE_MM, -MAX_DISTANCE_MM, MAX_DISTANCE_MM)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glPointSize(2.0)

def render():
    glClear(GL_COLOR_BUFFER_BIT)
    
    glBegin(GL_TRIANGLES)
    glColor3f(1.0, 1.0, 1.0)
    glVertex2f(-50, -50)
    glVertex2f(50, -50)
    glVertex2f(0, 100)
    glEnd()

    current_history = list(scan_history) 
    
    for i, scan in enumerate(reversed(current_history)):
        alpha = 1.0 - (i / HISTORY_SIZE)
        if alpha <= 0: continue

        glBegin(GL_LINE_STRIP)
        for x, y, dist in scan:
            r, g, b = get_rainbow_color(dist, MAX_DISTANCE_MM)
            glColor4f(r, g, b, alpha)
            glVertex2f(x, y)
        glEnd()

    pygame.display.flip()

def main():
    global running
    
    lidar_thread = LidarThread()
    lidar_thread.start()

    pygame.init()
    pygame.display.set_mode(WINDOW_SIZE, pygame.DOUBLEBUF | pygame.OPENGL)
    pygame.display.set_caption("Advanced Lidar Mapper V1.0")
    init_opengl()

    clock = pygame.time.Clock()
    
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
            
            render()
            clock.tick(60)
            
    except KeyboardInterrupt:
        pass
    finally:
        running = False
        lidar_thread.join()
        pygame.quit()

if __name__ == '__main__':
    main()

