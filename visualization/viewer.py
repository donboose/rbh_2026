import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import os

WINDOW_SIZE = (1024, 768)
DATA_FILE = "room_scan.rbtsof"
DRONE_SPEED = 1.0   
START_X = -6.0
END_X = 6.0      

class PointCloudViewer:
    def __init__(self):
        self.points = None
        self.colors = None
        self.timestamps = None
        
        self.current_time = 0.0
        self.is_playing = True
        self.visible_count = 0
        
        self.cam_pos = [0, -2, -12] 
        self.cam_rot = [0, 0]      
        self.mouse_down = False
        self.last_mouse_pos = (0, 0)
        
        self.init_window()
        self.init_opengl()
        self.load_data(DATA_FILE)

    def init_window(self):
        pygame.init()
        pygame.display.set_caption("LiDAR Tunnel Scan")
        pygame.display.set_mode(WINDOW_SIZE, DOUBLEBUF | OPENGL | RESIZABLE)

    def init_opengl(self):
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glPointSize(2) 
        self.resize_viewport(WINDOW_SIZE[0], WINDOW_SIZE[1])

    def resize_viewport(self, width, height):
        if height == 0: height = 1
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60, (width / height), 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)

    def load_data(self, filename):
        if not os.path.exists(filename):
            print("File not found.")
            return
        
        print("Loading data...")
        data = np.loadtxt(filename, dtype=np.float32)
        
        self.points = data[:, 0:3]
        self.colors = data[:, 3:6]
        self.timestamps = data[:, 6]
        
        self.total_points = len(self.points)
        self.max_time = np.max(self.timestamps)

    def update_simulation(self, dt):
        if not self.is_playing or self.points is None: return
        self.current_time += dt
        
        if self.current_time > self.max_time:
            self.current_time = self.max_time
            
        self.visible_count = np.searchsorted(self.timestamps, self.current_time)

    def draw_drone(self):
        drone_x = START_X + (self.current_time * DRONE_SPEED)
        
        if drone_x > END_X: return

        glPushMatrix()
        glTranslatef(drone_x, 2.0, 0) 
        glColor3f(1.0, 0.0, 0.0) 
        glLineWidth(2)
        
        glBegin(GL_LINES)
        s = 0.2
        vertices = [(-s,-s,-s),(s,-s,-s),(s,-s,s),(-s,-s,s),
                    (-s,s,-s),(s,s,-s),(s,s,s),(-s,s,s)]
        edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),
                 (0,4),(1,5),(2,6),(3,7)]
        for e in edges:
            glVertex3f(*vertices[e[0]])
            glVertex3f(*vertices[e[1]])
        glEnd()
        glPopMatrix()

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        glTranslatef(self.cam_pos[0], self.cam_pos[1], self.cam_pos[2])
        glRotatef(self.cam_rot[0], 1, 0, 0)
        glRotatef(self.cam_rot[1], 0, 1, 0)
        
        if self.points is not None and self.visible_count > 0:
            glEnableClientState(GL_VERTEX_ARRAY)
            glEnableClientState(GL_COLOR_ARRAY)
            glVertexPointer(3, GL_FLOAT, 0, self.points)
            glColorPointer(3, GL_FLOAT, 0, self.colors)
            glDrawArrays(GL_POINTS, 0, self.visible_count)
            glDisableClientState(GL_VERTEX_ARRAY)
            glDisableClientState(GL_COLOR_ARRAY)
            
        self.draw_drone()
        pygame.display.flip()

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == QUIT: return False
            elif event.type == VIDEORESIZE: self.resize_viewport(event.w, event.h)
            elif event.type == KEYDOWN:
                if event.key == K_SPACE: self.is_playing = not self.is_playing
                if event.key == K_r: self.current_time = 0
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1: self.mouse_down = True; self.last_mouse_pos = event.pos
                elif event.button == 4: self.cam_pos[2] += 1.0
                elif event.button == 5: self.cam_pos[2] -= 1.0
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1: self.mouse_down = False
            elif event.type == MOUSEMOTION:
                if self.mouse_down:
                    x, y = event.pos
                    dx, dy = x - self.last_mouse_pos[0], y - self.last_mouse_pos[1]
                    self.cam_rot[0] += dy * 0.2
                    self.cam_rot[1] += dx * 0.2
                    self.last_mouse_pos = (x, y)
        
        keys = pygame.key.get_pressed()
        s = 0.1
        if keys[K_w]: self.cam_pos[1] -= s
        if keys[K_s]: self.cam_pos[1] += s
        if keys[K_a]: self.cam_pos[0] += s
        if keys[K_d]: self.cam_pos[0] -= s
        return True

    def run(self):
        clock = pygame.time.Clock()
        while self.handle_input():
            dt = clock.tick(60) / 1000.0
            self.update_simulation(dt)
            self.draw()
        pygame.quit()

if __name__ == "__main__":
    viewer = PointCloudViewer()
    viewer.run()

