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




def make_transform_matrix(position=None, orientation=None):
    """
    Construct a 4x4 homogeneous transformation matrix.

    Parameters
    ----------
    position : (x, y, z), optional
        Translation in the parent's coordinate system.

    orientation : (3, 3) array or (azimuth, elevation, roll), optional
        Rotation specification.

        If a 3x3 array is supplied, it is used directly as the
        rotation matrix.

        If a 3-tuple is supplied, the values are interpreted as
        azimuth, elevation and roll angles in degrees.

        Convention:
            azimuth   = horizontal heading of local +z axis
            elevation = upward tilt of local +z axis
            roll      = rotation about the resulting local +z axis

        Azimuth is measured from world +x toward world +y.

    Returns
    -------
    T : (4, 4) ndarray
        Homogeneous transformation matrix mapping local coordinates
        into parent coordinates.
    """

    # Identity transformation
    T = np.eye(4)

    # Translation
    if position is not None:
        T[:3, 3] = np.asarray(position, dtype=float)

    # Rotation
    if orientation is not None:

        orientation = np.asarray(orientation)

        # Direct rotation-matrix form
        if orientation.shape == (3, 3):
            rot = orientation.astype(float)

        # Euler angles: Azimuth, elevation, roll form
        elif orientation.shape == (3,):
            rot = rotation_from_euler_angles(orientation)

        else:
            raise ValueError(
                "orientation must be either a 3-element "
                "(azimuth, elevation, roll) sequence or a 3x3 "
                "rotation matrix"
            )

        T[:3, :3] = rot

    return T

def transform_points(points, transform):
    """ Helper function to perform point transformations using homogeneous coordinates."""
    points = np.asarray(points, dtype=float)
    homogeneous = np.column_stack([
        points,
        np.ones(len(points))
    ])
    transformed = (transform @ homogeneous.T).T
    return transformed[:, :3]
