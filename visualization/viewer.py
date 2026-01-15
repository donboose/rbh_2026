import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import os
import imgui
from imgui.integrations.pygame import PygameRenderer
import array 

WINDOW_SIZE = (1280, 720)
DATA_FILE = "room_scan.rbtsof"
START_X = -6.0
END_X = 6.0      

class PointCloudViewer:
    def __init__(self):
        self.points = None
        self.colors = None
        self.original_colors = None
        self.timestamps = None
        self.motor_data = None
        
        self.current_time = 0.0
        self.is_playing = True
        self.visible_count = 0
        self.drone_speed = 1.0
        
        self.point_size = 2.0
        self.bg_color = [0.0, 0.0, 0.0]
        self.show_grid = False
        self.grid_size = 25
        self.show_x_axis = True
        self.show_y_axis = True
        self.show_z_axis = True
        self.use_heatmap = True
        
        self.hist_counts = np.array([], dtype=np.float32)
        self.motor_history = [array.array('f', [1500.0] * 100) for _ in range(4)]
        self.prev_visible_count = 0
        
        self.cam_pos = [0, -2, -12] 
        self.cam_rot = [0, 0]      
        self.mouse_down = False
        self.last_mouse_pos = (0, 0)
        
        self.init_window()
        self.init_opengl()
        self.init_imgui()
        self.load_data(DATA_FILE)

    def init_window(self):
        pygame.init()
        pygame.display.set_caption("LiDAR Mapping v1.5 - Motor Telemetry")
        pygame.display.set_mode(WINDOW_SIZE, DOUBLEBUF | OPENGL | RESIZABLE)

    def init_opengl(self):
        glEnable(GL_DEPTH_TEST)
        glPointSize(self.point_size)
        self.resize_viewport(WINDOW_SIZE[0], WINDOW_SIZE[1])

    def init_imgui(self):
        imgui.create_context()
        self.impl = PygameRenderer()

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
        data = np.loadtxt(filename, dtype=np.float32)
        
        self.points = data[:, 0:3]
        self.original_colors = data[:, 3:6]
        self.colors = self.original_colors.copy()
        self.timestamps = data[:, 6]
        
        if data.shape[1] >= 11:
            self.motor_data = data[:, 7:11]
        else:
            print("Warning: Old file format. No motor data found.")
            self.motor_data = np.full((len(data), 4), 1500.0)

        self.total_points = len(self.points)
        self.max_time = np.max(self.timestamps)

    def get_drone_position(self):
        drone_x = START_X + (self.current_time * self.drone_speed)
        return [drone_x, 2.0, 0.0]

    def update_heatmap_colors(self):
        if self.visible_count == 0: return
        drone_pos = self.get_drone_position()
        visible_points = self.points[:self.visible_count]
        diff = visible_points - np.array(drone_pos)
        dists = np.linalg.norm(diff, axis=1)
        norm_dists = np.clip((dists - 1.0) / 14.0, 0.0, 1.0)
        colors = np.zeros((len(visible_points), 3), dtype=np.float32)
        colors[:, 0] = norm_dists
        colors[:, 1] = 1.0 - np.abs(norm_dists - 0.5) * 2.0
        colors[:, 2] = 1.0 - norm_dists
        self.colors[:self.visible_count] = colors

    def update_graphs(self):
        """Updates Histogram and Motor Graphs."""
        if self.visible_count == 0: return

        y_values = self.points[:self.visible_count, 1] 
        counts, _ = np.histogram(y_values, bins=50, range=(0, 5))
        self.hist_counts = counts.astype(np.float32)

        if self.visible_count > self.prev_visible_count:
            new_motors = self.motor_data[self.prev_visible_count : self.visible_count]
            avg_signals = np.mean(new_motors, axis=0)
        else:
            avg_signals = [h[-1] for h in self.motor_history]

        self.prev_visible_count = self.visible_count
        
        for i in range(4):
            self.motor_history[i].pop(0)
            self.motor_history[i].append(float(avg_signals[i]))

    def update_simulation(self, dt):
        if not self.is_playing or self.points is None: return
        
        self.current_time += dt
        total_distance = END_X - START_X
        required_duration = total_distance / self.drone_speed
        
        if self.current_time > required_duration:
            self.current_time = required_duration
            self.is_playing = False
        
        effective_timestamp = self.current_time * self.drone_speed
        self.visible_count = np.searchsorted(self.timestamps, effective_timestamp)
        
        if self.use_heatmap: self.update_heatmap_colors()
        self.update_graphs()

    def draw_ui(self):
        imgui.new_frame()

        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File", True):
                if imgui.menu_item("Quit", "Cmd+Q", False, True)[0]: return False
                imgui.end_menu()
            if imgui.begin_menu("View", True):
                _, self.show_grid = imgui.menu_item("Show Grid", "", self.show_grid, True)
                _, self.show_x_axis = imgui.menu_item("Show X Axis", "", self.show_x_axis, True)
                _, self.show_y_axis = imgui.menu_item("Show Y Axis", "", self.show_y_axis, True)
                _, self.show_z_axis = imgui.menu_item("Show Z Axis", "", self.show_z_axis, True)
                imgui.separator()
                if imgui.menu_item("Reset Camera", "", False, True)[0]:
                    self.cam_pos = [0, -2, -12]; self.cam_rot = [0, 0]
                imgui.end_menu()
            imgui.end_main_menu_bar()

        imgui.begin("Configuration", True)
        if imgui.button("Pause" if self.is_playing else "Play"):
            self.is_playing = not self.is_playing
        if imgui.button("Restart"):
            self.current_time = 0.0; self.is_playing = True; self.prev_visible_count = 0
            self.hist_counts = np.array([], dtype=np.float32)
            self.motor_history = [array.array('f', [1500.0] * 100) for _ in range(4)]
            
        imgui.separator()
        if self.is_playing:
            imgui.text_colored("Pause to change speed", 0.7, 0.7, 0.7)
            imgui.slider_float("Scan Speed", self.drone_speed, 0.1, 5.0)
        else:
            changed, self.drone_speed = imgui.slider_float("Scan Speed", self.drone_speed, 0.1, 5.0)

        imgui.separator()
        clicked_heat, self.use_heatmap = imgui.checkbox("Heatmap Mode", self.use_heatmap)
        if clicked_heat:
            if self.use_heatmap: self.update_heatmap_colors()
            else: self.colors[:self.visible_count] = self.original_colors[:self.visible_count]
            
        changed, self.bg_color = imgui.color_edit3("Background", *self.bg_color)
        changed, self.point_size = imgui.slider_float("Point Size", self.point_size, 1.0, 10.0)
        changed, self.grid_size = imgui.slider_int("Grid Size", self.grid_size, 5, 50)
        imgui.end()

        imgui.begin("Real-time Analytics", True)
        
        imgui.text("Height Distribution")
        if len(self.hist_counts) > 0:
            imgui.plot_histogram("Height", self.hist_counts, graph_size=(0, 60), scale_min=0.0)
            
        imgui.separator()
        imgui.text("Motor Signals (PWM)")
        imgui.text_colored("Front Motors (Low Pitch)", 0.6, 0.8, 1.0)
        imgui.plot_lines("M1", self.motor_history[0], graph_size=(0, 40), scale_min=1300, scale_max=1700)
        imgui.plot_lines("M2", self.motor_history[1], graph_size=(0, 40), scale_min=1300, scale_max=1700)
        
        imgui.text_colored("Rear Motors (High Pitch)", 1.0, 0.6, 0.6)
        imgui.plot_lines("M3", self.motor_history[2], graph_size=(0, 40), scale_min=1300, scale_max=1700)
        imgui.plot_lines("M4", self.motor_history[3], graph_size=(0, 40), scale_min=1300, scale_max=1700)
        
        imgui.end()

        imgui.render()
        self.impl.render(imgui.get_draw_data())
        return True

    def draw_grid(self):
        glLineWidth(1); glColor3f(0.3, 0.3, 0.3); glBegin(GL_LINES); s = self.grid_size
        for i in range(-s, s+1): glVertex3f(i,0,-s); glVertex3f(i,0,s); glVertex3f(-s,0,i); glVertex3f(s,0,i)
        glEnd()

    def draw_axes(self):
        glLineWidth(3); glBegin(GL_LINES)
        if self.show_x_axis: glColor3f(1,0,0); glVertex3f(0,0,0); glVertex3f(5,0,0)
        if self.show_y_axis: glColor3f(0,1,0); glVertex3f(0,0,0); glVertex3f(0,5,0)
        if self.show_z_axis: glColor3f(0,0,1); glVertex3f(0,0,0); glVertex3f(0,0,5)
        glEnd()

    def draw_scene(self):
        glClearColor(*self.bg_color, 1.0); glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity(); glPointSize(self.point_size)
        glTranslatef(*self.cam_pos); glRotatef(self.cam_rot[0], 1, 0, 0); glRotatef(self.cam_rot[1], 0, 1, 0)
        if self.show_grid: self.draw_grid()
        self.draw_axes()
        if self.points is not None and self.visible_count > 0:
            glEnableClientState(GL_VERTEX_ARRAY); glEnableClientState(GL_COLOR_ARRAY)
            glVertexPointer(3, GL_FLOAT, 0, self.points); glColorPointer(3, GL_FLOAT, 0, self.colors)
            glDrawArrays(GL_POINTS, 0, self.visible_count)
            glDisableClientState(GL_VERTEX_ARRAY); glDisableClientState(GL_COLOR_ARRAY)
        drone_pos = self.get_drone_position()
        if drone_pos[0] <= END_X:
            glPushMatrix(); glTranslatef(*drone_pos); glColor3f(1,0,0); glLineWidth(2); glBegin(GL_LINES); s=0.2
            v=[(-s,-s,-s),(s,-s,-s),(s,-s,s),(-s,-s,s),(-s,s,-s),(s,s,-s),(s,s,s),(-s,s,s)]
            e=[(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
            for ed in e: glVertex3f(*v[ed[0]]); glVertex3f(*v[ed[1]])
            glEnd(); glPopMatrix()

    def run(self):
        clock = pygame.time.Clock(); running = True
        while running:
            for event in pygame.event.get():
                self.impl.process_event(event)
                if event.type == QUIT: running = False
                elif event.type == VIDEORESIZE: self.resize_viewport(event.w, event.h)
                if not imgui.get_io().want_capture_mouse:
                    if event.type == MOUSEBUTTONDOWN:
                        if event.button == 1: self.mouse_down = True; self.last_mouse_pos = event.pos
                        elif event.button == 4: self.cam_pos[2] += 1.0
                        elif event.button == 5: self.cam_pos[2] -= 1.0
                    elif event.type == MOUSEBUTTONUP:
                        if event.button == 1: self.mouse_down = False
                    elif event.type == MOUSEMOTION and self.mouse_down:
                        x, y = event.pos; dx, dy = x - self.last_mouse_pos[0], y - self.last_mouse_pos[1]
                        self.cam_rot[0] += dy * 0.2; self.cam_rot[1] += dx * 0.2; self.last_mouse_pos = (x, y)
            keys = pygame.key.get_pressed(); s = 0.1
            if keys[K_w]: self.cam_pos[1] -= s
            if keys[K_s]: self.cam_pos[1] += s
            if keys[K_a]: self.cam_pos[0] += s
            if keys[K_d]: self.cam_pos[0] -= s
            dt = clock.tick(60) / 1000.0
            self.update_simulation(dt); self.draw_scene(); running = self.draw_ui(); pygame.display.flip()
        pygame.quit()

if __name__ == "__main__":
    viewer = PointCloudViewer()
    viewer.run()

