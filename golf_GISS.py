from tkinter import*;from tkinter.filedialog import*;c=Canvas();c.pack();f=askopenfilenames()
for o in __import__('shapefile').Reader(f[0]).shapes():
 for l in map(lambda s:str(s)[10:-2].replace(', ',',').replace(' ',',').split(','),__import__('shapely.geometry',(),(),['']).shape(o)):
  p=lambda g:__import__('pyproj').Proj(init='epsg:3395')(*g);c.create_polygon(sum(((p(x)[0],-p(x)[1])for x in zip(l[0::2],l[1::2])),()))
c.bind('<MouseWheel>',lambda e:c.scale('all',e.x,e.y,(e.delta>0)*2or 0.5,(e.delta>0)*2or 0.5));mainloop()