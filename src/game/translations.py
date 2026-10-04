#!/bin/env python3

import numpy as np

# -----------------------------------------------------
# Auxiliary functions for constructing transformation matrices
def rotation_from_euler_angles(angles_deg):
    az, el, roll = np.deg2rad(angles_deg)

    caz = np.cos(az)
    saz = np.sin(az)

    cel = np.cos(el)
    sel = np.sin(el)

    cr = np.cos(roll)
    sr = np.sin(roll)

    # Rotation about world Z: azimuth
    Rz_az = np.array([
        [caz, -saz, 0.0],
        [saz,  caz, 0.0],
        [0.0,  0.0, 1.0],
    ])

    # Rotation about Y.
    #
    # The negative sign is intentional: with our convention
    # positive elevation tilts local +z upward.
    Ry_el = np.array([
        [ cel, 0.0, -sel],
        [ 0.0, 1.0,  0.0],
        [ sel, 0.0,  cel],
    ])

    # Roll about the local +z axis
    Rz_roll = np.array([
        [cr, -sr, 0.0],
        [sr,  cr, 0.0],
        [0.0, 0.0, 1.0],
    ])

    # Local -> parent rotation
    rot = Rz_az @ Ry_el @ Rz_roll
    return rot