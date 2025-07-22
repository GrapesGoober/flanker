import type { Vec2 } from '$lib';
import * as d3 from 'd3';

export function generatePointsInsidePolygon(
	coords: Vec2[],
	spacing: number,
	jitter: number
): Vec2[] {
	const xs = coords.map((p) => p.x);
	const ys = coords.map((p) => p.y);
	const [minX, maxX] = [Math.min(...xs), Math.max(...xs)];
	const [minY, maxY] = [Math.min(...ys), Math.max(...ys)];

	// Polygon array for D3
	const d3Coords: [number, number][] = coords.map(({ x, y }) => [x, y]);

	const result: Vec2[] = [];
	for (let x = minX; x <= maxX; x += spacing) {
		for (let y = minY; y <= maxY; y += spacing) {
			const maxAttempts = 10;

			// Keep jittering until falls falls inside
			for (let attempt = 0; attempt < maxAttempts; attempt++) {
				const jitterX = (Math.random() - 0.5) * jitter;
				const jitterY = (Math.random() - 0.5) * jitter;
				const point = { x: x + jitterX, y: y + jitterY };

				if (d3.polygonContains(d3Coords, [point.x, point.y])) {
					result.push(point);
					break;
				}
			}
		}
	}
	return result;
}

export function generateEvenPointsInsidePolygon(
	coords: Vec2[],
	numpoints: number,
	jitter_multiplier: number,
	minSpacing: number = 15,
	maxSpacing: number = 200
): Vec2[] {
	if (coords.length < 3 || numpoints <= 0) return [];

	let bestPoints: Vec2[] = [];

	for (let i = 0; i < 20; i++) {
		// max 20 iterations
		const midSpacing = (minSpacing + maxSpacing) / 2;
		const jitter = midSpacing * jitter_multiplier;
		const points = generatePointsInsidePolygon(coords, midSpacing, jitter);

		if (points.length === numpoints) {
			return points;
		}

		bestPoints = points;

		// Too many points => Spacing is too small
		if (points.length > numpoints) {
			minSpacing = midSpacing;
		}
		// Too few points => Spacing is too large
		else {
			maxSpacing = midSpacing;
		}
	}

	return bestPoints;
}
