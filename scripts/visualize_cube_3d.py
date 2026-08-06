from __future__ import annotations

from typing import Final

import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int_]


def generate_cube(
    center: tuple[float, float, float] = (0.0, 0.0, 0.0),
    side_length: float = 1.0,
) -> tuple[FloatArray, IntArray]:

    if side_length <= 0:
        raise ValueError("side_length must be positive.")

    cx, cy, cz = center
    h = side_length / 2.0

    vertices = np.array(
        [
            [cx - h, cy - h, cz - h],
            [cx + h, cy - h, cz - h],
            [cx + h, cy + h, cz - h],
            [cx - h, cy + h, cz - h],
            [cx - h, cy - h, cz + h],
            [cx + h, cy - h, cz + h],
            [cx + h, cy + h, cz + h],
            [cx - h, cy + h, cz + h],
        ],
        dtype=np.float64,
    )

    edges = np.array(
        [
            [0, 1],
            [1, 2],
            [2, 3],
            [3, 0],
            [4, 5],
            [5, 6],
            [6, 7],
            [7, 4],
            [0, 4],
            [1, 5],
            [2, 6],
            [3, 7],
        ],
        dtype=np.int_,
    )

    return vertices, edges


def plot_cube(
    vertices: FloatArray,
    edges: IntArray,
) -> None:
    """
    Render a cube using Matplotlib.
    """
    fig = plt.figure(figsize=(6, 6))  # type: ignore
    ax = fig.add_subplot(111, projection="3d")

    # Draw edges
    for start, end in edges:
        pts = vertices[[start, end]]
        ax.plot(  # type: ignore
            pts[:, 0],
            pts[:, 1],
            pts[:, 2],
            linewidth=2.0,
        )

    # Draw vertices
    ax.scatter(  # type: ignore
        xs=vertices[:, 0],
        ys=vertices[:, 1],
        # matplotlib stub shenanigans
        zs=vertices[:, 2],  # type: ignore
        s=50,
    )

    # Equal aspect ratio
    mins = vertices.min(axis=0)
    maxs = vertices.max(axis=0)
    center = (mins + maxs) / 2.0
    radius: Final = float(np.max(maxs - mins) / 2.0)

    ax.set_xlim(center[0] - radius, center[0] + radius)  # type: ignore
    ax.set_ylim(center[1] - radius, center[1] + radius)  # type: ignore
    ax.set_zlim(center[2] - radius, center[2] + radius)  # type: ignore
    ax.set_box_aspect((1.0, 1.0, 1.0))  # type: ignore

    ax.set_xlabel("X")  # type: ignore
    ax.set_ylabel("Y")  # type: ignore
    ax.set_zlabel("Z")  # type: ignore

    plt.show()  # type: ignore


def main() -> None:
    vertices, edges = generate_cube(
        center=(0.0, 0.0, 0.0),
        side_length=2.0,
    )
    plot_cube(vertices, edges)


if __name__ == "__main__":
    main()
