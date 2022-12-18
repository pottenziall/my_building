from dataclasses import dataclass, fields
from typing import Tuple, Optional, List, Any
import re
import pandas as pd

from enum import Enum


MATERIALS = [("concrete", 10, "m3"), ("brick", 11, "m3"), ("faced_brick", 15, "m3"), ("window", 100, "m2"), ("door", 60, "peace")]


@dataclass
class Connection:
    objects: Tuple[Any, Any]

    def volume(self):
        volume = 0
        for obj in self.objects:
            if not isinstance(obj, Layer):
                for layer in obj:
                    volume += self._volume()


class Quantity(Enum):
    M3 = "m3"
    M2 = "m2"
    P = "peace"


@dataclass
class Material:
    name: str
    price: float
    price_quantity: Quantity


class Side(Enum):
    TOP = "xy+"
    BOTTOM = "xy-"
    FRONT = "xz-"
    REAR = "xz+"
    LEFT = "yz-"
    RIGHT = "yz+"


class Axis(Enum):
    L = "l"
    W = "w"
    H = "h"


@dataclass
class Dimension:
    axis: Axis
    quantity: int
    _is_scaled: bool = False

    def __post_init__(self):
        assert Axis.__contains__(self.axis), f"Value must be instance of {Axis}: {self.axis}"
        assert self.quantity > 0, f"Dimension must be > 0: {self.quantity}"

    def scaled(self, scale: int):
        assert scale > 0, f"Scale must be > 0: {scale}"
        if self._is_scaled:
            raise AssertionError("Value already scaled")
        self._is_scaled = True
        return self.quantity * scale
        
    def __add__(self, other):
        assert isinstance(other, Dimension), f"Other must be instance of {self.__class__}: {type(other)}"
        assert self.axis == other.axis, f"Only the same dimensions can be combined: {self.axis, other.axis}"
        return Dimension(self.axis, self.quantity + other.quantity)


@dataclass
class CoordSet:
    x1: int
    y1: int
    z1: int
    x2: int
    y2: int
    z2: int

    def __post_init__(self):
        for value in [self.x1, self.y1, self.z1, self.x2, self.y2, self.z2]:
            assert value >= 0, f"Coordinate shouldn't less than zero: {value}"

    def __iter__(self):
        self._i = 0
        return self

    def __next__(self):
        return [self.x1, self.y1, self.z1, self.x2, self.y2, self.z2][self._i]


@dataclass
class Layer:
    name: str
    material: Material
    exterior: Side
    connections: List[Any]
    coords: CoordSet

    def dimensions(self) -> Tuple[Dimension, ...]:
        length = abs(self.coords.x2 - self.coords.x1)
        width = abs(self.coords.y2 - self.coords.y1)
        height = abs(self.coords.z2 - self.coords.z1)
        if width > length:
            length, width = width, length
        return Dimension(Axis.L, length), Dimension(Axis.W, width), Dimension(Axis.H, height)

    # side area
    def area(self) -> int:
        if self.exterior in [Side.FRONT, Side.REAR]:
            return abs(self.coords.x2 - self.coords.x1) * abs(self.coords.z2 - self.coords.z1)
        elif self.exterior in [Side.LEFT, Side.RIGHT]:
            return abs(self.coords.y2 - self.coords.y1) * abs(self.coords.z2 - self.coords.z1)
        elif self.exterior in [Side.TOP, Side.BOTTOM]:
            return abs(self.coords.x2 - self.coords.x1) * abs(self.coords.y2 - self.coords.y1)
        else:
            raise AssertionError(f"Exterior argument must belong to {Side}: {self.exterior}")

    @property
    def volume(self) -> int:
        value = 1
        for d in self.dimensions():
            value = d.quantity * value
        return value

    def scaled(self, scale: Optional[int] = 1) -> Tuple[Dimension, ...]:
        assert scale > 0, f"Scale must be > 0: {scale}"
        dimensions = []
        for d in self.dimensions():
            dimensions.append(Dimension(d.axis, d.scaled(scale)))
        return tuple(dimensions)

    def cost(self) -> float:
        if self.material.price_quantity == Quantity.M3:
            return self.volume * self.material.price
        elif self.material.price_quantity == Quantity.M2:
            return self.area() * self.material.price
        elif self.material.price_quantity == Quantity.P:
            return self.material.price
        else:
            raise AssertionError(f"Wrong price quantity of the material: {self.material.price_quantity}")


@dataclass
class LayerMinus(Layer):

    def volume(self) -> int:
        volume = super(LayerMinus, self).volume
        return - volume


@dataclass
class Wall:
    name: str
    _layers: List[Layer]

    def __post_init__(self):
        assert self._layers, "At least one layer should be added to Wall"
        wrong_objects = [layer for layer in self._layers if not isinstance(layer, Layer)]
        assert not wrong_objects, f"Wrong object(s) passed to {self.__class__}: {wrong_objects}"

    def _check_layer(self, other: Layer):
        for x, xo in zip():


    def add_layer(self, layer: Layer):
        assert isinstance(layer, Layer), f"Layer object should be passed: {layer}"
        self._layers.append(layer)

    def remove_layer(self, layer: str):
        layer_to_remove = [l for l in self._layers if l.name == layer]
        assert layer_to_remove, f"{layer} not found in the Wall layers"
        self._layers.remove(layer_to_remove[0])

    def volume(self):
        volumes = [layer.volume for layer in self._layers]
        return sum(volumes)

    def dimensions(self):
        dimensions = []
        for i in range(3):
            dimension = 0
            for layer in self._layers:
                # TODO: ckeck axis before adding
                dimension += layer.dimensions()[i]
            dimensions.append(dimension)
        return dimensions

    def coords(self):
        data = [layer.coords for layer in self._layers]
        df = pd.DataFrame(data)
        return CoordSet(min(df[0]), min(df[1]), min(df[2]), max(df[3]), max(df[4]), max(df[5]))



@dataclass
class Window(LayerMinus):
    price: float

    def cost(self) -> float:
        return self.price * self.area()


@dataclass
class Door(LayerMinus):
    price: float

    def cost(self) -> float:
        return self.price * self.area()



#
# @dataclass
# class Layer(Volume):
#     touch_side: Side
#
#     def __add__(self, other) -> Volume:
#         assert isinstance(other, Volume), f"Other must be instance of Volume: {type(other)}"
#         l1, w1, h1 = [d.quantity for d in self.dimensions]
#         l2, w2, h2 = [d.quantity for d in other.dimensions]
#         if self.touch_side.value.startswith("l"):  # length1 + length2
#             l1 = l1 + l2
#         elif self.touch_side.value.startswith("w"):
#             w1 = w1 + w2
#         else:
#             h1 = h1 + h2
#         return Volume(l1, w1, h1)


if __name__ == '__main__':
    a = Layer(1,1,1)
    b = Layer(1, 1, 2)
    w = Wall("nord", Side.REAR, [a,b])
    c = CoordSet(1,2,3,4,5,6)
    vol = w.volume()
    print(vol)
