import numpy as np
from dataclasses import dataclass, field
from copy import copy

from .translations import make_transform_matrix, rotation_from_z_axis

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
# Skeleton constructors
class Joint:
    """
    A point in a skeleton/structure.

    position is the rest position, expressed in the coordinate system
    of the Skeleton.
    """

    def __init__(self, name, position):
        self.name = name
        self.rest_position = np.asarray(position, dtype=float)

        # Current position is initially the rest position.
        #
        # Later this can be replaced by a pose/transform system.
        self.position = self.rest_position.copy()

        self.connections = []

    def __repr__(self):
        return f"Joint({self.name!r}, {self.position.tolist()})"


# ----------------------------------------------------------------------
# Connection
# ----------------------------------------------------------------------

class Connection:
    """
    Generic relationship between two joints.
    """

    def __init__(self, name, joint_a, joint_b):
        self.name = name
        self.joint_a = joint_a
        self.joint_b = joint_b

        joint_a.connections.append(self)
        joint_b.connections.append(self)

    @property
    def vector(self):
        return self.joint_b.position - self.joint_a.position

    @property
    def length(self):
        return np.linalg.norm(self.vector)


# ----------------------------------------------------------------------
# Beam
# ----------------------------------------------------------------------

class Beam(Connection):
    """
    Rigid connection between two joints.

    rest_length is retained explicitly because it will eventually be
    useful for physics / IK / constraint solving.
    """

    def __init__(self, name, joint_a, joint_b, radius=0.04):
        super().__init__(name, joint_a, joint_b)

        self.rest_length = self.length
        self.radius = radius

    def __repr__(self):
        return (
            f"Beam({self.name!r}, "
            f"{self.joint_a.name!r} -> {self.joint_b.name!r}, "
            f"L={self.rest_length:.3f})"
        )


# ----------------------------------------------------------------------
# Skeleton
# ----------------------------------------------------------------------

class Skeleton:
    """
    Graph of joints and connections.

    The graph is deliberately independent of Element / rendering.
    """

    def __init__(self, name="skeleton"):
        self.name = name

        self.joints = {}
        self.connections = []

    # ------------------------------------------------------------------

    def add_joint(self, name, position):
        if name in self.joints:
            raise ValueError(f"Joint already exists: {name}")

        joint = Joint(name, position)
        self.joints[name] = joint

        return joint

    # ------------------------------------------------------------------

    def add_beam(self, name, joint_a, joint_b, radius=0.04):
        """
        joint_a and joint_b may either be Joint objects or joint names.
        """

        if isinstance(joint_a, str):
            joint_a = self.joints[joint_a]

        if isinstance(joint_b, str):
            joint_b = self.joints[joint_b]

        beam = Beam( name,joint_a,joint_b, radius=radius,)
        self.connections.append(beam)

        return beam

    # ------------------------------------------------------------------

    def add(self, connection):
        self.connections.append(connection)
        return connection

    # ------------------------------------------------------------------

    def print_graph(self):
        print(f"Skeleton: {self.name}")
        print()

        print("Joints:")
        for joint in self.joints.values():
            p = joint.position
            print(
                f"  {joint.name:12s}"
                f" [{p[0]:7.3f}, {p[1]:7.3f}, {p[2]:7.3f}]"
            )

        print()
        print("Connections:")

        for connection in self.connections:
            print(
                f"  {connection.name:16s}"
                f" {connection.joint_a.name:12s}"
                f" -> {connection.joint_b.name:12s}"
                f"  L={connection.length:.3f}"
            )

    # ------------------------------------------------------------------

    def to_element(self):
        """
        Convert the skeleton into a renderable Element hierarchy.
        Every Beam becomes a cylinder between its two joints.
        The returned Element represents the completeskeleton
        coordinates.
        """
        new_elem = Element(self.name)
        for beam in self.connections:
            if not isinstance(beam, Beam):
                continue

            p0 = beam.joint_a.position
            p1 = beam.joint_b.position

            beam_elem = make_beam_element(
                name=beam.name,
                p0=p0,
                p1=p1,
                radius=beam.radius,
            )

            new_elem.add(beam_elem)

        return new_elem

#-----------
#HELPERS - not cylinder should be primative constructor
def cylinder_geometry(length, radius, n=12):
    """
    Make a cylinder of the specified length and radius.
    The cylinder lies along +Z.
    """

    theta = np.linspace( 0.0,2.0 * np.pi, n,endpoint=False,)

    circle = np.column_stack([
        radius * np.cos(theta),
        radius * np.sin(theta),
        np.zeros(n),
    ])

    top = circle.copy()
    top[:, 2] = length

    points = np.vstack([circle, top,])

    faces = []
    # Bottom and Bottom
    faces.append(np.arange(n - 1, -1, -1))
    faces.append(np.arange(n, 2 * n))

    # Sides
    for i in range(n):
        j = (i + 1) % n
        faces.append([i,j,n + j,n + i,])

    return Geometry(points, faces)



def make_beam_element(name, p0, p1, radius):
    """
    Construct a cylindrical Element representing a Beam from p0 to p1.
    """

    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)

    vector = p1 - p0
    length = np.linalg.norm(vector)

    if length <= 1e-12:
        raise ValueError(
            f"Beam {name!r} has zero length"
        )

    geometry = cylinder_geometry(length=length, radius=radius,)
    transform = rotation_from_z_axis(vector)
    transform[:3, 3] = p0

    style = Style(
        face_color=(120, 90, 60),
        edge_color=(30, 30, 30),
        edge_width=1,
    )

    return Element(
        name=name,
        geometry=geometry,
        transform=transform,
        style=style,
    )


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




