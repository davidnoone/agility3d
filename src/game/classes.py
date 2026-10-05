import numpy as np
from dataclasses import dataclass, field
from copy import copy

from .translations import make_transform_matrix
from . import serializer as serializer


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

    def find(self, name):
        if self.name == name:
            return self
        for child in self.children:
            result = child.find(name)
            if result is not None:
                return result
        return None

    def walk(self, parent_transform=None):
        if parent_transform is None:
            parent_transform = np.eye(4)
            
        world_transform = parent_transform @ self.transform

        yield self, world_transform
        for child in self.children:
            yield from child.walk(world_transform)


    def save(self,filename):
        serializer.save(self, filename)

    @classmethod
    def load(cls, filename):
        return serializer.load(filename)


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



#===========================================================
# GROUP OF BEHAVIOURS: stpre needed metadata, and the "update" method
class BehaviourMotion:
    """ Holds meta data about Elements' bahavioud/motion/dynamics """
    def __init__(self, element):
        self.element = element

        self.u = 5000.0        # mm/s, local +x (forward)
        self.v = 0.0        # mm/s, local +y (left)
        self.omega_z = 90.0  # degrees/s, rotation about local +z

    def update(self, dt):
        # position
        dpos = [dt*self.u, dt*self.v, 0]    # no up/down (mm/sec)

        # heading
        dtheta = dt*self.omega_z          # Spin in x-y plane (deg/sec)

        c = np.cos(np.radians(dtheta))
        s = np.sin(np.radians(dtheta))

        rot = np.array([
            [ c, -s, 0],
            [ s,  c, 0],
            [ 0,  0, 1],
        ])

        dT = make_transform_matrix(position=dpos, orientation=rot)

        # Apply the translation
        self.element.transform = self.element.transform @ dT


#=========================================
# Once the classes are defined, they can be registered for serialization
serializer.register_class(Style)
serializer.register_class(Geometry)
serializer.register_class(Element)




