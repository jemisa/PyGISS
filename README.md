# Introduction

A Geographic Information System (GIS) software is a software designed to import, analyze and visualize geographic data.
PyGISS is a lightweight GIS software based on the standard Python library for GUI programming: tkinter.
It allows users to create maps by importing shapefiles (.shp files), a format that describes maps as a set of polygons.

# PyGISS dependencies

PyGIS relies on three Python libraries:

* pyshp, used for reading shapefiles.
* shapely, used for converting a multipolygons into a set of polygons
* pyproj, used for translating geographic coordinates (longitude and latitude) into projected coordinates

Before using PyGISS, you must make sure all these libraries are properly installed:

```
pip install pyshp
pip install shapely
pip install pyproj
```

# PyGISS versions

## Standard version (pyGISS.py, < 100 lines)

The standard version implements PyGISS in less than 100 lines of code.

It contains 
* a menu 'Import shapefile' for the user to choose a shapefile and draw maps.
* a menu 'Switch projection' to switch between the mercator and azimuthal orthographic projection.

The right-click button allows the user to move the display in any direction, and the scroll wheel to zoom in and out.
A left-click button on the map will print the associated geographical coordinates (longitude, latitude).

## Golf version (golf_GISS, 5 lines)

The golf version implements the mercator projection
