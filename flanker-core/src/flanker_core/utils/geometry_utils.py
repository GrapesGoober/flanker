import math

from flanker_core.models.components import Transform
from flanker_core.models.vec2 import Vec2
from flanker_core.utils.intersect_utils import IntersectUtils


class GeometryUtils:

    @staticmethod
    def clip_by_fov_cone(
        polyline: list[Vec2],
        center_point: Vec2,
        heading_degree: float,
        fov_degree: int = 90,
        radius: float = 1000,
    ) -> list[Vec2]:
        """Returns a new clipped a polygon to the specified cone."""

        # Create some rays that defines this FOV cone
        heading_rad = math.radians(heading_degree)
        forward_direction: Vec2 = Vec2(1, 0).rotated(heading_rad)
        forward_ray = forward_direction * radius
        half_angle_rad = math.radians(fov_degree / 2)
        left_ray: Vec2 = center_point + forward_ray.rotated(half_angle_rad)
        right_ray: Vec2 = center_point + forward_ray.rotated(-half_angle_rad)

        # Choose the two first intersection points of this FOV cone
        left_point = min(
            IntersectUtils.get_intersects(
                line=(center_point, left_ray), polyline=polyline
            ),
            key=lambda point: (center_point - point).length(),
        )
        right_point = min(
            IntersectUtils.get_intersects(
                line=(center_point, right_ray), polyline=polyline
            ),
            key=lambda point: (center_point - point).length(),
        )

        # Filter LOS polygon of any points outside of FOV
        threshold_rad: float = math.cos(half_angle_rad)
        new_los: list[Vec2] = []
        for vertex in polyline:
            direction = vertex - center_point

            if direction.length() < 1e-9:
                # Keep the center point
                new_los.append(vertex)
                continue

            # Using dot formula to filter the angle
            a: Vec2 = forward_direction
            b: Vec2 = direction.normalized()
            if a.dot(b) >= threshold_rad:
                new_los.append(vertex)

        # Add left points and right points back to the list
        # to represent the cut FOV edges.
        new_los.append(left_point)
        new_los.append(right_point)
        new_los.append(center_point - forward_direction * 1e-9)
        new_los = GeometryUtils.sort_verts_by_angle(center_point, new_los)
        new_los.append(new_los[0])  # Loop back to a closed polyline
        return new_los

    @staticmethod
    def in_fov(
        origin_transform: Transform,
        target_pos: Vec2,
        fov: float = 90,
    ) -> bool:
        """
        Util method returns `True` if the position `target_pos`
        is in FOV cone of origin position `origin_transform`.
        """

        # Direction the spotter is facing
        heading_rad = math.radians(origin_transform.degrees)
        forward_dir: Vec2 = Vec2(1, 0).rotated(heading_rad)

        # Direction to target
        to_target = (target_pos - origin_transform.position).normalized()

        # Dot product -> angle check
        dot = forward_dir.dot(to_target)

        # cos(theta) comparison (avoid expensive acos)
        half_fov_rad = math.radians(fov / 2)
        return dot >= math.cos(half_fov_rad)

    @staticmethod
    def sort_verts_by_angle(
        center_point: Vec2,
        verts: list[Vec2],
    ) -> list[Vec2]:
        """Sort vertices by the angle from a point."""

        def angle_from_center(v: Vec2) -> float:
            rel = v - center_point
            theta = math.atan2(rel.y, rel.x)
            if theta < 0:
                theta += 2 * math.pi
            return theta

        return sorted(verts, key=angle_from_center)
