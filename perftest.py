# Vanilla dataclass
from dataclasses import dataclass
from enum import Enum

# from pydantic import BaseModel
from pydantic import BaseModel


class Bar(str, Enum):
    BAR = "BAR"


@dataclass
class Foo:
    x: int
    y: str
    b: Bar = Bar.BAR


class FooModel(BaseModel):
    x: int
    y: str


# Timing comparison
import time

NUM_POINTS = 1_000_000

print("Test creation")
# Dataclass
t0 = time.time()
m1 = [Foo(x=1, y="hi") for _ in range(NUM_POINTS)]
print("Dataclass:", time.time() - t0)

# Pydantic
t0 = time.time()
m2 = [FooModel(x=1, y="hi") for _ in range(NUM_POINTS)]
print("Pydantic:", time.time() - t0)

print("Test assignments")
t0 = time.time()
for m in m1:
    m.x = 1
    m.y = "bar"
print("Dataclass:", time.time() - t0)

t1 = time.time()
for m in m2:
    m.x = 1
    m.y = "bar"

print("pydantic:", time.time() - t1)
