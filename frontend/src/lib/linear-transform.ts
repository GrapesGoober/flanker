import type { Vec2 } from '$lib/api';

export function transform(vecList: Vec2[], translate: Vec2, rotate: number): Vec2[] {
	const radians = (rotate * Math.PI) / 180;
	const cosA = Math.cos(radians);
	const sinA = Math.sin(radians);

	return vecList.map((vec) => ({
		x: vec.x * cosA - vec.y * sinA + translate.x,
		y: vec.x * sinA + vec.y * cosA + translate.y
	}));
}
