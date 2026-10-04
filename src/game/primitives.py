#!/bin/env python3

#
# Defines geometry for primitive objects
#

import numpy as np
from .classes import Geometry



#==========================================================
# PUBLIC INTERFACE: Create Geometry object from named 2d polygon function
#==========================================================

def geom2d(points_func, z=0, *args, **kwargs):
    """Construct planar 3D Geometry from a 2D points function."""
    points_xy = np.asarray(points_func(*args, **kwargs), dtype=float)

    if points_xy.ndim != 2 or points_xy.shape[1] != 2:
        raise ValueError("2D points function must return an (N, 2) array")

    npts = points_xy.shape[0]
    points = np.column_stack([points_xy, np.full(npts, z), ])
    faces = [np.arange(npts, dtype=int) ]
    return Geometry(points, faces)


#==========================================================
# EXTRUDE FUNCTION: returns Geometry object.
#==========================================================

def extrude(points_xy, z):
    """Extrude a 2D polygon in the xy-plane along +z.

    Parameters
    ----------
    points : array_like, shape (n, 2) i.e., (x, y) pairs
        Polygon vertices in counterclockwise order as viewed from +z.
    z : float
        Extrusion distance along +z.
    """
    points = np.asarray(points_xy, dtype=float)
    npts = len(points_xy)

    # Bottom and top vertices
    bottom_points = np.column_stack([points_xy, np.zeros(npts)])       # (x,y,0)
    top_points    = np.column_stack([points_xy, np.full(npts, z) ])    # (x, y, z=z)
    all_points    = np.vstack([bottom_points, top_points])


    # Bottom and top faces
    bottom_face = np.arange(npts)           # Loop of points on the bottom
    top_face    = np.arange(npts, 2*npts)   # Loop of poits on the top

    # Side faces: for a closed polygn of npts, there are npts rectangular faces
    side_faces = []
    for i in range(npts):
        j = (i + 1) % npts
        side_faces.append([ i, j, npts + j,  npts + i,])

    # Points are wound CCW viewed from +z:
    #   top    -> outward normal +z
    #   bottom -> outward normal -z  (so, reverse order, notice ::-1 below)
    faces =[ bottom_face[::-1], top_face, *side_faces, ]  # note sequence unpacking "*"

    return Geometry(all_points, faces)



#==========================================================
# Generate primitive prisms by extrusion: make 2d polygon, then eextrude
#==========================================================

def cylinder(radius,length, npts=32):
    return extrude(points_circle(radius, npts=npts), length)

def cube(x):
    return extrude(points_square(x),x)

def rectangle(x, y, z):
    return extrude(points_rectangle(x,y),z)
#    return extrude(points_mitre(x,y),z)     # defaut 90 degree cuts!

def mitre_prism(x, y, z, deg_left=90, deg_right=90, ):
    return extrude(points_mitre(x,y, deg_left=deg_left, deg_right=deg_right),z)

def parallelogram(x, y, z, deg_cut=90):
    return extrude(points_mitre(x,y, deg_left=deg_cut, deg_right=deg_cut),z)

def trapazoid(x, y, z, deg_cut=90):
    return extrude(points_mitre(x,y, deg_left=deg_cut, deg_right=180-deg_cut),z)

def corregated(x, y, z, nwave=6, thick=1):
    return extrude(points_nsheet(x,y,thick=thick, nwave=nwave),z)




def points_triangle(x, y, offset=0):
    """ Triangle base in x, height in y, with optional offset for midpoint.
    Use height = 0.866*base for equillateral, or use npoly(npts=3)
    """
    apex = x/2 + offset
    xpts = [0, x,   apex]
    ypts = [0,    0,   y]
    return np.column_stack([xpts, ypts])

def points_npoly(radius, npts=3): 
    """ N sided polygon: 3 triangle, 4 diamon, 5 pentagon, 6 hexagon, ....infinity circle! 
    Convention sets point origin at center - DIFFERS FROM RECTANGLES"""
    t = 2.0*np.pi * np.arange(npts)/ npts
    xpts = radius * np.cos(t)
    ypts = radius * np.sin(t)
    return np.column_stack([xpts, ypts])

def points_circle(radius, npts=32): 
    return points_npoly(radius, npts=npts)

def points_square(x):
    """ A square is a special rectangle, or npoly(npts=4) """
    return points_rectangle(x,x)

def points_rectangle(x,y):
    """ Rectangle """
    xpts = [0, x, x, 0]
    ypts = [0, 0, y, y]
    return np.column_stack([xpts, ypts])

def points_mitre(x, y, deg_left=90, deg_right=90):
    """ Rectangle with mitre cut ends: x sets uncut/envelope rectangle length.
        Allows cases of parallelogram, trapesoid, rhombus, .... """
    if (deg_left < 0  ) or (deg_right < 0  ) or \
       (deg_left > 180) or (deg_right > 180):
        raise ValueError("MITRE: cut angles must be between 0 and 180 (positive)",deg_left, deg_right)
    
    dx_left =  y*np.cos(np.radians(deg_left))
    x0 = 0
    x3 = dx_left        # might be negtaive

    dx_right = y*np.cos(np.radians(deg_right))
    x1 = 0
    x2 = dx_right        # might be negtaive

    # Set length, as a bounding box, allowing for diagonal cut outs
    cut_left = max(-dx_left,0)      # upper overhand on the left
    cut_right = max(dx_right, 0)    # upper overhang on the right
    uncut = x - cut_left - cut_right
    if (uncut < 0):
        raise ValueError('MITRE: stock length "x" is insufficient for needed cuts.')
    x1 += uncut
    x2 += uncut

    xpts = [x0, x1, x2, x3]
    ypts = [ 0, 0 , y , y ]
    return np.column_stack([xpts, ypts])


def points_notched(x, y, xnotch, dx, dy, top=False):
    """Notched rectangle, with notch starting at xnotch,
    of width dx and depth dy."""
    if not (x > 0 and y > 0):
        raise ValueError("x and y must be positive")
    if not (0 <= xnotch < x):
        raise ValueError("xnotch must lie within the rectangle")
    if not (0 < dx and xnotch + dx < x):
        raise ValueError("notch must lie within the rectangle")
    if not (0 < dy < y):
        raise ValueError("dy must lie between 0 and y")

    if top:
        xpts = [0, x, x, xnotch+dx, xnotch+dx, xnotch, xnotch, 0]
        ypts = [0, 0, y,         y,       y-dy,   y-dy,      y, y]
    else:
        xpts = [0, xnotch, xnotch, xnotch+dx, xnotch+dx, x, x]
        ypts = [0, 0,      y-dy,   y-dy,      y,         y, 0]

    return np.column_stack([xpts, ypts])


def points_birdsmouth(x,y, dx=0, dy=0):
    """ Birdsmouthed rectangle: angled/triangle notch. """
    raise ValueError("Not implimented")

def points_ibeam(x,y, dx=0, dy=None):
    """ I-beam """
    if dy is None: dy = dx
    if not (x > 0 and y > 0):
        raise ValueError("IBEAM: x and y must be positive")
    if (dx > 0.5*x):
        raise ValueError("IBEAM x thickness must be less than half X")
    if (dy > 0.5*y):
        raise ValueError("IBEAM y thickness must be less than half y")
    xpts = [0, x,   x, x-dx, x-dx,    x,  x, 0,  0,      dx, dx, 0 ]
    ypts = [0, 0,  dy,   dy, y-dy, y-dy,  y, y,  y-dy, y-dy, dy, dy]
    return np.column_stack([xpts, ypts])

def points_hbeam(x,y, dx=0, dy=0):
    """ I beam, on the side"""
    return points_ibeam(y,x, dx=dy, dy=dx)

def points_nsheet(x, y, thick=1, nwave=7, npts=32): 
    """ Corregated sheeting: nwave = npts/2 gives triangle """
    amp = 0.5*y - thick
    f = np.arange(npts)/(npts-1)    # include end
    t = 2.0*np.pi*nwave*f
    acost = amp*np.cos(t)
    xpts = np.asarray([  x*f, x*f[:,:-1] ])
    ypts = np.asarray([acost-0.5*thick, acost[::-1]+0.5*thick])
    return np.column_stack([xpts, ypts])


#=============================================================
# Direct constructor for a rectangular prism to show point definition and winding
def rectangular_prism_direct(x, y, z):
    points = np.array([
        [0, 0, 0],
        [x, 0, 0],
        [0, y, 0],
        [x, y, 0],
        [0, 0, z],
        [x, 0, z],
        [0, y, z],
        [x, y, z],
    ])

    faces = np.array([
        [2, 3, 1, 0],  # bottom: -z
        [5, 7, 6, 4],  # top:    +z
        [1, 5, 4, 0],  # front:  -y
        [6, 7, 3, 2],  # back:   +y
        [4, 6, 2, 0],  # left:   -x
        [3, 7, 5, 1],  # right:  +x
    ])

    return Geometry(points, faces)
#=============================================================
