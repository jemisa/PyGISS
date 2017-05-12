import sys
import tkinter as tk
try:
    import shapefile
    import shapely.geometry
    import pyproj
except ImportError:
    sys.exit(1)

class Map(tk.Canvas):

    projections = {
    'mercator': pyproj.Proj(init="epsg:3395"),
    'spherical': pyproj.Proj('+proj=ortho +lat_0=47 +lon_0=28')
    }
    
    def __init__(self, root):
        super().__init__(root, bg='white', width=1300, height=800)
        self.projection = 'mercator'
        self.scale, self.offset = 1, (0, 0)
        self.pack()
        
        menu = tk.Menu(root)
        menu.add_command(label="Import shapefile", command=self.import_map)
        root.config(menu=menu)
        
    def import_map(self):
        fielpath = tk.filedialog.askopenfilenames(title='Import shapefile')

                    filepath ,= filepath
        
    def draw_map(self):
        self.delete_map()
        self.draw_water()
        for shape in self.yield_shapes():
            str_shape = str(shape)[10:-2].replace(', ', ',').replace(' ', ',')
            list_shape = str_shape.replace('(', '').replace(')', '').split(',')
            self.draw_land(list_shape)
                
    def yield_shapes(self):        
        sf = shapefile.Reader(self.shapefile)       
        shapes = sf.shapes() 
        for shape in shapes:
            shape = shapely.geometry.shape(shape)
            if shape.geom_type == 'MultiPolygon':
                yield from shape
            else:
                yield shape

    def scale_map(self, ratio, event):
        self.scale *= float(ratio)
        offset_x, offset_y = self.offset
        self.offset = (offset_x*ratio + event.x*(1 - ratio), 
                       offset_y*ratio + event.y*(1 - ratio))

    def change_projection(self, projection):
        self.scale, self.offset = 1, (0, 0)
        self.projection = projection
        self.draw_map()
        
    def draw_land(self, land):
        coords = (self.to_canvas_coordinates(*c) for c in zip(land[0::2], land[1::2]))
        obj_id = self.cvs.create_polygon(sum(coords, tuple()), fill='green3', 
                                            outline='black', tags=('land',))

    def draw_water(self):
        if self.projection == 'mercator':
            x0, y0 = self.to_canvas_coordinates(-180, 84)
            x1, y1 = self.to_canvas_coordinates(180, -84)
            self.water_id = self.cvs.create_rectangle(x1, y1, x0, y0,
                        outline='black', fill='deep sky blue', tags=('water',))
        else:
            cx, cy = self.to_canvas_coordinates(28, 47)
            self.water_id = self.cvs.create_oval(cx - 6378000, cy - 6378000, 
                                cx + 6378000, cy + 6378000, outline='black', 
                                        fill='deep sky blue', tags=('water',))
            
    def delete_map(self):
        self.cvs.delete('land', 'water')
        
    def to_canvas_coordinates(self, longitude, latitude):
        px, py = self.projections[self.projection](longitude, latitude)
        return px*self.scale + self.offset[0], -py*self.scale + self.offset[1]
        
    def to_geographical_coordinates(self, x, y):
        px, py = (x - self.offset[0])/self.scale, (self.offset[1] - y)/self.scale
        return self.projections[self.projection](px, py, inverse=True)
        
if str.__eq__(__name__, '__main__'):
    root_window = tk.Tk()
    root_window.title('PyGISS: A GIS software in less than 100 lines of Python')
    py_GISS = Map(root_window)
    root_window.mainloop()