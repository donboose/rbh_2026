import os
import math
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from rplidar import RPLidar
import time

PORT_NAME = '/dev/ttyUSB0' 
WINDOW_SIZE = (800, 600)
MAX_DISTANCE_MM = 6000 # 6 m

def process_data(scan):
    """Converts polar (angle, dist) to cartesian (x, y)"""
    points = []
    for quality, angle, distance in scan:
        if distance > 0:
            angle_rad = math.radians(angle)
            x = distance * math.cos(angle_rad)
            y = distance * math.sin(angle_rad)
            points.append((x, y))
    return points

def init_opengl():
    """Sets up a 2D orthographic view for mapping"""
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-MAX_DISTANCE_MM, MAX_DISTANCE_MM, -MAX_DISTANCE_MM, MAX_DISTANCE_MM)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glPointSize(2.0)

def run():
    lidar = RPLidar(PORT_NAME)
    pygame.init()
    pygame.display.set_mode(WINDOW_SIZE, pygame.DOUBLEBUF | pygame.OPENGL)
    pygame.display.set_caption("RPLidar Ground Test - PyOpenGL")
    
    init_opengl()

    print("Starting Lidar scan... Press ESC to quit.")
    
    try:
        lidar.stop()
        lidar.stop_motor()
        lidar.clean_input()

        time.sleep(1)
        for scan in lidar.iter_scans():
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    raise KeyboardInterrupt

            glClear(GL_COLOR_BUFFER_BIT)

            points = process_data(scan)
            
            glBegin(GL_POINTS)
            glColor3f(0.0, 1.0, 0.0)
            for x, y in points:
                glVertex2f(x, y)
            
            glColor3f(1.0, 0.0, 0.0) 
            glVertex2f(0, 0)
            glEnd()

            pygame.display.flip()

    except KeyboardInterrupt:
        print("Stopping...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        lidar.stop()
        lidar.stop_motor()
        lidar.disconnect()
        pygame.quit()

if __name__ == '__main__':
    run()

