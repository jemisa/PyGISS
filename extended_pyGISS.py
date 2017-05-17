import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
try:
    import pyproj
    import shapefile
    import shapely.geometry
except ImportError:
    import sys
    from tkinter import messagebox
    tk.messagebox.showinfo('Some libraries are missing', 
                    'Pyproj, Shapefile and Shapely are required (see README)')
    sys.exit(1)
    
class Controller(tk.Tk):
    
    def __init__(self):
        super().__init__()
        self.title('Extended PyGISS: A full-on GIS software')
        
        for widget in (
                       'Button',
                       'Label', 
                       'Labelframe', 
                       'Labelframe.Label', 
                       ):
            ttk.Style().configure('T' + widget, background='lavender')
        
        self.menu = Menu(self)
        self.menu.pack(side='left', fill='both', expand=1)
        
        self.map = Map(self)
        self.map.pack(fill='both', expand=1)
        
        menu = tk.Menu(self)
        menu.add_command(label="Import shapefile", command=self.map.import_map)
        menu.add_command(label="Switch projection", command=self.map.switch_proj)
        self.config(menu=menu)
        
class Menu(tk.Frame):
    
    def __init__(self, controller):            
        super().__init__(controller)
        self.configure(background='lavender')   

        # label frame for object creation
        lf_selection = ttk.Labelframe(self)
        lf_selection.text = 'Object creation'
        lf_selection.grid(row=1, column=0, sticky='nsew')
        
        ttk.Label(self, text='test').grid(row=0, column=0, in_=lf_selection)
        
class Map(tk.Canvas):

    projections = {
    'mercator': pyproj.Proj(init="epsg:3395"),
    'spherical': pyproj.Proj('+proj=ortho +lon_0=28 +lat_0=47')
    }
    
    def __init__(self, controller):
        super().__init__(controller, bg='white', width=1300, height=800)
        self.proj = 'mercator'
        self.ratio, self.offset = 1, (0, 0)
        self.bind('<ButtonPress-1>', self.print_coords)
        self.bind('<MouseWheel>', self.zoomer)
        self.bind('<Button-4>', lambda e: self.zoomer(e, 1.3))
        self.bind('<Button-5>', lambda e: self.zoomer(e, 0.7))
        self.bind('<ButtonPress-3>', lambda e: self.scan_mark(e.x, e.y))
        self.bind('<B3-Motion>', lambda e: self.scan_dragto(e.x, e.y, gain=1))
        
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
        
    def print_coords(self, event):
        event.x, event.y = self.canvasx(event.x), self.canvasy(event.y)
        print(*self.to_geographical_coordinates(event.x, event.y))
        
    def zoomer(self, event, factor=None):
        if not factor: 
            factor = 1.3 if event.delta > 0 else 0.7
        event.x, event.y = self.canvasx(event.x), self.canvasy(event.y)
        self.scale('all', event.x, event.y, factor, factor)
        self.configure(scrollregion=self.bbox('all'))
        self.ratio *= float(factor)
        self.offset = (self.offset[0]*factor + event.x*(1 - factor), 
                       self.offset[1]*factor + event.y*(1 - factor))
        
if str.__eq__(__name__, '__main__'):
    controller = Controller()
    controller.mainloop()