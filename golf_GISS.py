from tkinter import*;w=Tk();c=Canvas(w,width=1500,height=900);c.pack();from tkinter import filedialog as d;f=d.askopenfilenames()
for o in __import__('shapefile').Reader(f[0]).shapes():
 for l in __import__('shapely.geometry',(),(),['']).shape(o):
  l=str(l)[10:-2].replace(', ',',').replace(' ',',').split(',');p=lambda c:__import__('pyproj').Proj(init='epsg:3395')(*c)
  c.create_polygon(sum(((p(c)[0],-p(c)[1])for c in zip(l[0::2],l[1::2])),()))
c.bind('<MouseWheel>',lambda e:c.scale('all',e.x,e.y,(e.delta>0)*2or 0.5,(e.delta>0)*2or 0.5));w.title('pyGISS in 6 lines');mainloop()