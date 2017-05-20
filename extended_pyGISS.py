import sys
import tkinter as tk
from inspect import stack
from os.path import abspath, dirname, pardir, join
from PIL import ImageTk
from tkinter import ttk, filedialog
try:
    import pyproj
    import shapefile
    import shapely.geometry
except ImportError:
    from tkinter import messagebox
    tk.messagebox.showinfo('Some libraries are missing', 
                    'Pyproj, Shapefile and Shapely are required (see README)')
    sys.exit(1)
    
# prevent python from writing *.pyc files / __pycache__ folders
sys.dont_write_bytecode = True

path_app = dirname(abspath(stack()[0][1]))

if path_app not in sys.path:
    sys.path.append(path_app)
    
class Controller(tk.Tk):
    
    def __init__(self, path_app):
        super().__init__()
        self.title('Extended PyGISS: A full-on GIS software')
        path_icon = abspath(join(path_app, 'icons'))
        
        # generate the PSF tk images
        img_psf = ImageTk.Image.open(join(
                                          path_icon, 
                                          'node.png'
                                          )
                                    )
                                    
        selected_img_psf = ImageTk.Image.open(join(
                                          path_icon, 
                                          'selected_node.png'
                                          )
                                    )
        self.psf_button_image = ImageTk.PhotoImage(img_psf.resize((100, 100)))
        self.node_image = ImageTk.PhotoImage(img_psf.resize((40, 40)))
        self.selected_node_image = ImageTk.PhotoImage(selected_img_psf.resize((40, 40)))
        
        for widget in (
                       'Button',
                       'Label', 
                       'Labelframe', 
                       'Labelframe.Label', 
                       ):
            ttk.Style().configure('T' + widget, background='#A1DBCD')
        
        self.menu = Menu(self)
        self.menu.pack(side='left', fill='both', expand=1)
        
        self.map = Map(self)
        self.map.pack(fill='both', expand=1)
        
        menu = tk.Menu(self)
        menu.add_command(label="Import shapefile", command=self.map.import_map)
        menu.add_command(label="Switch projection", command=self.map.switch_proj)
        self.config(menu=menu)
        
        # if motion is called, the left-click button was released and we 
        # can stop the drag and drop process
        self.bind_all('<Motion>', self.stop_drag_and_drop)
        self.bind_all('<B1-Motion>', lambda _: _)
        self.drag_and_drop = False
            
    def stop_drag_and_drop(self, event):
        self.drag_and_drop = False
        
    def start_drag_and_drop(self, event):
        self.drag_and_drop = True
        
class Menu(tk.Frame):
    
    def __init__(self, controller):            
        super().__init__(controller)
        self.configure(background='#A1DBCD')   

        lf_creation = ttk.Labelframe(
                                     self, 
                                     text = 'Object creation', 
                                     padding = (6, 6, 12, 12)
                                     )
        lf_creation.grid(row=0, column=0, sticky='nsew')
        
        psf_object_label = tk.Label(
                               self, 
                               image = controller.psf_button_image, 
                               relief = 'flat', 
                               bg = '#A1DBCD'
                               )
        psf_object_label.bind('<Button-1>', controller.start_drag_and_drop)
        psf_object_label.grid(row=0, column=0, sticky='ns', in_=lf_creation)
        
        lf_projection = ttk.Labelframe(
                                       self, 
                                       text = 'Projection settings', 
                                       padding = (6, 6, 12, 12)
                                       )
        lf_projection.grid(row=1, column=0, sticky='nsew')
        
        change_projection_button = tk.Button(self, text='Change projection')
        change_projection_button.grid(row=0, column=0, in_=lf_projection)
        
class Map(tk.Canvas):

    projections = {
    'mercator': pyproj.Proj(init="epsg:3395"),
    'spherical': pyproj.Proj('+proj=ortho +lon_0=28 +lat_0=47')
    }
    
    def __init__(self, controller):
        super().__init__(controller, bg='white', width=1300, height=800)
        self.controller = controller
        
        self.node_id_to_node = {}
        self.drag_item = None
        self.start_position = [None]*2
        self.start_pos_main_node = [None]*2
        self.dict_start_position = {}
        self.selected_nodes = set()
        
        self.proj = 'mercator'
        self.ratio, self.offset = 1, (0, 0)
        self.bind('<MouseWheel>', self.zoomer)
        self.bind('<Button-4>', lambda e: self.zoomer(e, 1.3))
        self.bind('<Button-5>', lambda e: self.zoomer(e, 0.7))
        self.bind('<ButtonPress-3>', lambda e: self.scan_mark(e.x, e.y))
        self.bind('<B3-Motion>', lambda e: self.scan_dragto(e.x, e.y, gain=1))
        self.bind('<Enter>', self.drag_and_drop, add='+')
        self.bind('<ButtonPress-1>', self.start_point_select_objects, add='+')
        self.bind('<B1-Motion>', self.rectangle_drawing)
        self.bind('<ButtonRelease-1>', self.end_point_select_nodes, add='+')
        self.tag_bind('node', '<Button-1>', self.find_closest_node)
        self.tag_bind('node', '<B1-Motion>', self.node_motion)
        
    # @update_coordinates decorator
    def update_coordinates(function):
        def wrapper(self, event, *others):
            event.x, event.y = self.canvasx(event.x), self.canvasy(event.y)
            function(self, event, *others)
        return wrapper
        
    def to_canvas_coordinates(self, longitude, latitude):
        px, py = self.projections[self.proj](longitude, latitude)
        return px*self.ratio + self.offset[0], -py*self.ratio + self.offset[1]
        
    def to_geographical_coordinates(self, x, y):
        px, py = (x - self.offset[0])/self.ratio, (self.offset[1] - y)/self.ratio
        return self.projections[self.proj](px, py, inverse=True)
                
    def import_map(self):
        self.filepath ,= tk.filedialog.askopenfilenames(title='Import shapefile')
        self.draw_map()
        
    def draw_map(self):
        self.delete('land', 'water')
        self.draw_water()
        sf = shapefile.Reader(self.filepath)       
        polygons = sf.shapes() 
        for polygon in polygons:
            polygon = shapely.geometry.shape(polygon)
            if polygon.geom_type == 'Polygon':
                polygon = [polygon]
            for land in polygon:
                land = str(land)[10:-2].replace(', ', ',').replace(' ', ',')
                coords = land.replace('(', '').replace(')', '').split(',')
                self.create_polygon(
                                    sum((self.to_canvas_coordinates(*c) 
                                    for c in zip(coords[0::2], coords[1::2])), ()),    
                                    fill = 'green3', 
                                    outline = 'black', 
                                    tags = ('land',)
                                    )

    def draw_water(self):
        if self.proj == 'mercator':
            x0, y0 = self.to_canvas_coordinates(-180, 84)
            x1, y1 = self.to_canvas_coordinates(180, -84)
            self.water_id = self.create_rectangle(x1, y1, x0, y0,
                        outline='black', fill='deep sky blue', tags=('water',))
        else:
            cx, cy = self.to_canvas_coordinates(28, 47)
            R = 6378000*self.ratio
            self.water_id = self.create_oval(cx - R, cy - R, cx + R, cy + R,
                        outline='black', fill='deep sky blue', tags=('water',))
        
    def switch_proj(self):
        self.proj = 'mercator' if self.proj == 'spherical' else 'spherical'
        self.draw_map()
        
    @update_coordinates
    def zoomer(self, event, factor=None):
        if not factor: 
            factor = 1.3 if event.delta > 0 else 0.7
        self.scale('all', event.x, event.y, factor, factor)
        self.configure(scrollregion=self.bbox('all'))
        self.ratio *= float(factor)
        self.offset = (self.offset[0]*factor + event.x*(1 - factor), 
                       self.offset[1]*factor + event.y*(1 - factor))
        # we update all node's coordinates
        for node_id, node in self.node_id_to_node.items():
            node.x, node.y = self.coords(node_id)
            self.update_node_label(node, 20)
                       
    def drag_and_drop(self, event):
        if controller.drag_and_drop:
            self.create_object(event)
            controller.drag_and_drop = False
                        
    @update_coordinates
    def create_object(self, event):
        # create the node's image
        id = self.create_image(
                               event.x - 20, 
                               event.y - 20,
                               image = controller.node_image, 
                               anchor = 'nw', 
                               tags = ('node',)
                               )
        # create the node's label
        label_id = self.create_text(
                                    event.x - 5, 
                                    event.y + 30
                                    )
        # create the node object
        node = PSF_Object(id, label_id, event.x, event.y)
        # update the value of its label
        self.update_node_label(node)
        # store the node in the 'node ID' |-> node dictionnary
        self.node_id_to_node[id] = node
        
    def update_node_label(self, node, translate=0):
        lon, lat = self.to_geographical_coordinates(node.x, node.y)
        label = '({:.5f}, {:.5f})'.format(lon, lat)
        self.coords(node.label_id, node.x - 5 + translate, node.y + 30 + translate)
        self.itemconfig(node.label_id, text=label)
                    
    @update_coordinates
    def find_closest_node(self, event):
        self.dict_start_position.clear()
        self.drag_item = self.find_closest(event.x, event.y)[0]
        main_node_selected = self.node_id_to_node[self.drag_item]
        self.start_pos_main_node = event.x, event.y
        if main_node_selected in self.selected_nodes:
            for sn in self.selected_nodes:
                self.dict_start_position[sn] = [sn.x, sn.y]
        else:
            self.unselect_all()
            self.dict_start_position[main_node_selected] = self.start_pos_main_node 
            self.select_objects(main_node_selected)
            
    def select_objects(self, *objects):
        for obj in objects:
            self.selected_nodes.add(obj)
            self.itemconfig(
                            obj.id, 
                            image = self.controller.selected_node_image
                            )
                
    def unselect_objects(self, *objects):
        for obj in objects:
            self.selected_nodes.discard(obj)
            self.itemconfig(
                            obj.id, 
                            image = self.controller.node_image
                            )
                
    def unselect_all(self):
        self.unselect_objects(*self.selected_nodes)
        
    @update_coordinates
    def start_point_select_objects(self, event):
        # create the temporary line, only if there is nothing below
        # this is to avoid drawing a rectangle when moving a node
        below = self.find_overlapping(event.x-1, event.y-1, event.x+1, event.y+1)
        tags_below = ''.join(''.join(self.itemcget(id, 'tags')) for id in below)
        # if no object is below the selection process can start
        if 'node' not in tags_below:
            self.unselect_all()
            self.start_position = event.x, event.y
            self.temp_rectangle = self.create_rectangle(
                                                        event.x, 
                                                        event.y, 
                                                        event.x, 
                                                        event.y
                                                        )
            self.tag_raise(self.temp_rectangle)

    @update_coordinates
    def rectangle_drawing(self, event):
        # draw the line only if they were created in the first place
        if self.start_position != [None]*2:
            # update the position of the temporary lines
            x0, y0 = self.start_position
            self.coords(self.temp_rectangle, x0, y0, event.x, event.y)
    
    @update_coordinates
    def end_point_select_nodes(self, event):
        if self.start_position != [None]*2:
            # delete the temporary lines
            self.delete(self.temp_rectangle)
            # select all nodes enclosed in the rectangle
            start_x, start_y = self.start_position
            for obj in self.find_enclosed(start_x, start_y, event.x, event.y):
                if obj in self.node_id_to_node:
                    enclosed_obj = self.node_id_to_node[obj]
                    self.select_objects(enclosed_obj)
            self.start_position = [None]*2
            
    @update_coordinates
    def node_motion(self, event):
        node = self.node_id_to_node[self.drag_item]
        for selected_node in self.selected_nodes:
            # the main node initial position, the main node current position, 
            # and the other node initial position form a rectangle.
            # we find the position of the fourth vertix.
            x0, y0 = self.start_pos_main_node
            x1, y1 = self.dict_start_position[selected_node]
            selected_node.x = x1 + (event.x - x0)
            selected_node.y = y1 + (event.y - y0)
            # move the node itself
            self.coords(
                        selected_node.id, 
                        selected_node.x - 20,
                        selected_node.y - 20
                        )
            # update the label
            self.update_node_label(selected_node)
        
class PSF_Object():
    
    type = 'node'
        
    def __init__(self, id, label_id, x, y):
        self.id = id
        self.label_id = label_id
        self.x = x
        self.y = y
        
if str.__eq__(__name__, '__main__'):
    controller = Controller(path_app)
    controller.mainloop()