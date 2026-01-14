import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import os

WINDOW_SIZE = (1024, 768)
POINT_SIZE = 2
BACKGROUND_COLOR = (0.05, 0.05, 0.1, 1.0)
DATA_FILE = "room_scan.rbtsof"

class PointCloudViewer:
    def __init__(self):
        self.points = None
        self.colors = None
        
        self.cam_pos = [0, -2, -15] # x, y (height), z (zoom)
        self.cam_rot = [20, 0]      # Pitch (20deg down), Yaw
        self.last_mouse_pos = (0, 0)
        self.mouse_down = False
        
        self.init_window()
        self.init_opengl()
        
        self.load_from_file(DATA_FILE)

    def init_window(self):
        pygame.init()
        pygame.display.set_caption(f"LiDAR Viewer - {DATA_FILE}")
        pygame.display.set_mode(WINDOW_SIZE, DOUBLEBUF | OPENGL | RESIZABLE)

    def init_opengl(self):
        glEnable(GL_DEPTH_TEST)
        glClearColor(*BACKGROUND_COLOR)
        glPointSize(POINT_SIZE)
        self.resize_viewport(WINDOW_SIZE[0], WINDOW_SIZE[1])

    def resize_viewport(self, width, height):
        if height == 0: height = 1
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60, (width / height), 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)

    def load_from_file(self, filename):
        """Loads X Y Z R G B data from a text file."""
        if not os.path.exists(filename):
            print(f"Error: {filename} not found. Run generate_room.py first!")
            self.points = np.array([[0,0,0]], dtype=np.float32)
            self.colors = np.array([[1,1,1]], dtype=np.float32)
            return

        print(f"Loading {filename}...")
        try:
            data = np.loadtxt(filename, dtype=np.float32)
            
            # Split into Points (cols 0,1,2) and Colors (cols 3,4,5)
            self.points = data[:, 0:3]
            self.colors = data[:, 3:6]
            
            print(f"Successfully loaded {len(self.points)} points.")
            
        except Exception as e:
            print(f"Failed to load file: {e}")

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == VIDEORESIZE:
                self.resize_viewport(event.w, event.h)
            
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1: # Left Click
                    self.mouse_down = True
                    self.last_mouse_pos = event.pos
                elif event.button == 4: # Zoom In
                    self.cam_pos[2] += 1.0
                elif event.button == 5: # Zoom Out
                    self.cam_pos[2] -= 1.0
            
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouse_down = False

            elif event.type == MOUSEMOTION:
                if self.mouse_down:
                    x, y = event.pos
                    dx = x - self.last_mouse_pos[0]
                    dy = y - self.last_mouse_pos[1]
                    self.cam_rot[0] += dy * 0.2
                    self.cam_rot[1] += dx * 0.2
                    self.last_mouse_pos = (x, y)
        
        keys = pygame.key.get_pressed()
        speed = 0.1
        if keys[K_w]: self.cam_pos[1] -= speed # Up/Down relative to screen
        if keys[K_s]: self.cam_pos[1] += speed
        if keys[K_a]: self.cam_pos[0] += speed
        if keys[K_d]: self.cam_pos[0] -= speed

        return True

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        glTranslatef(self.cam_pos[0], self.cam_pos[1], self.cam_pos[2])
        glRotatef(self.cam_rot[0], 1, 0, 0)
        glRotatef(self.cam_rot[1], 0, 1, 0)
        
        if self.points is not None:
            glEnableClientState(GL_VERTEX_ARRAY)
            glEnableClientState(GL_COLOR_ARRAY)
            glVertexPointer(3, GL_FLOAT, 0, self.points)
            glColorPointer(3, GL_FLOAT, 0, self.colors)
            glDrawArrays(GL_POINTS, 0, len(self.points))
            glDisableClientState(GL_VERTEX_ARRAY)
            glDisableClientState(GL_COLOR_ARRAY)
        
        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        while self.handle_input():
            self.draw()
            clock.tick(60)
        pygame.quit()

if __name__ == "__main__":
    viewer = PointCloudViewer()
    viewer.run()

