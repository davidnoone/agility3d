import numpy as np
from dataclasses import dataclass, field
from copy import copy

from .translations import rotation_from_euler_angles

@dataclass
class Style:
    face_color: tuple = (190, 150, 100)
    edge_color: tuple = (30, 30, 30)
    edge_width: int = 1
    alpha: float = 1.0
    visible: bool = True            # not used
    show_edges: bool = True         # not used


class Geometry:
    """
    Polygon mesh geometry.

    points:
        Nx3 array of vertices.

    faces:
        List of arrays containing vertex indices.
        Each face may have any number of vertices >= 3.

        Vertex winding follows the right-hand rule.
    """
    points: np.ndarray   # (npts,3) for 2d points
    faces: list          # list of (varying length) numpy int arrays

    def __init__(self, points, faces):
        if points.ndim != 2 or points.shape[1] != 3:
            raise ValueError("Geometry init(): points must have shape (N, 3)")

        self.points = np.asarray(points, dtype=float)
        self.faces = [np.asarray(face, dtype=int) for face in faces ]


class Element:
    """
    An element or assembly in the model.

    An Element may be used as a prototype. When added to another
    Element, a copy is made and given its own assembly-specific name
    and parent-relative transform.

    Parameters
    ----------
    geometry : Geometry, optional (exclude of Element is an assembly)
        Geometry belonging to this element, expressed in local coordinates.
    name : str, optional
        Name of this element when used as a prototype, or its name
        within its parent assembly when it is an instance.
    transform : (4, 4) array, optional
        Transformation from this element's local coordinates into
        its parent's coordinate system.
    """
    name: str = None
    prototype: str = None
    geometry: Geometry = None
    transform: np.ndarray = field(default_factory=lambda: np.eye(4))
    style: Style = field(default_factory=Style)
    children: list = field(default_factory=list)

    def __init__(self, name, geometry=None, transform=None, style=None):

        self.name = name
        self.prototype = None
        self.geometry = geometry 
        self.style = style or Style()       # default
        self.behaviour = None

        if transform is None:
            self.transform = np.eye(4)
        else:
            if transform.shape != (4, 4):   # validate
                raise ValueError("transform must be a 4x4 matrix")
            self.transform = np.asarray(transform, dtype=float)

        self.children = []

    def copy(self):
        """
        Make an independent copy of this Element.
        Geometry is shared between the prototype and the copy.
        Transform and child Elements are copied.
        """
        element = Element(self.name, 
            geometry=self.geometry,
            transform=self.transform.copy(),
            style = copy(self.style)
        )
        element.prototype = self.prototype      # Only assigned at copy

        element.children = [
            child.copy()
            for child in self.children
        ]

        return element

    def add( self, element, name=None, position=(0, 0, 0), orientation=(0, 0, 0),):
        """
        Add a copy of `element` as a child of this Element.

        Parameters
        ----------
        element : Element
            Prototype Element to copy.

        name : str, optional
            Name of this particular instance within this assembly.
            If omitted, the prototype's name is retained.

        position : (3,)
            Position of the child's local origin in this parent's
            coordinate system.

        orientation : tuple
            Orientation of the child relative to this parent.

        Returns
        -------
        Element
            The newly created child instance.
        """

        child = element.copy()

        # Preserve the name of the element from which this instance was created.
        if child.prototype is None:
            child.prototype = child.name

        if name is not None:
            child.name = name

        # Compose with any transform already belonging to the prototype.
        # Transforms map from local coordinates toward parent/world coordinates, using column vectors.
        T = make_transform_matrix( position, orientation,  )
        child.transform = T @ child.transform

        self.children.append(child)
        return child

    def remove(self, name):
        raise ValueError('Element.remove() not implemeted')


    def walk(self, parent_transform=None):
        if parent_transform is None:
            parent_transform = np.eye(4)
            
        world_transform = parent_transform @ self.transform

        yield self, world_transform

        for child in self.children:
            yield from child.walk(world_transform)


    def print_tree(self, verbose=False):
        """Print the Element hierarchy."""
        branch_cont = "|   "
        branch_fork = "|-- "
        branch_last = "o-- "

        def _print(element, prefix="", branch=""):

            if element.geometry is None:
                description = "assembly"
            else:
                npoints = len(element.geometry.points)
                nfaces = len(element.geometry.faces)
                description = f"{npoints} points, {nfaces} faces"

            name = (
                f'{element.name:<16}'
                if element.name is not None
                else "<unnamed>"
            )
            if element.prototype is not None:
                name += f" (prototype={element.prototype})"

            position = element.transform[:3, 3]

            print(
                f"{prefix}{branch}"
                f"{name} ({description})"
                f"  position={position}"
            )

            if verbose:
                print(f"{prefix}    transform:")

                for row in element.transform:
                    print( f"{prefix}      {row}" )

            for i, child in enumerate(element.children):

                last = i == len(element.children) - 1

                if last:
                    child_branch = branch_last
                    child_prefix = prefix + "    "
                else:
                    child_branch = branch_fork
                    child_prefix = prefix + branch_cont

                _print(
                    child,
                    prefix=child_prefix,
                    branch=child_branch,
                )

        _print(self)



def transform_points(points, transform):
    """ Helper function to perform point transformations using homogeneous coordinates."""
    points = np.asarray(points, dtype=float)
    homogeneous = np.column_stack([
        points,
        np.ones(len(points))
    ])
    transformed = (transform @ homogeneous.T).T
    return transformed[:, :3]


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