from dataclasses import dataclass


@dataclass
class Transform:
    position: tuple[float, float, float]
    rotation: tuple[float, float, float]


@dataclass
class RenderObject:
    name: str
    transform: Transform
    geometry: str = "cube"