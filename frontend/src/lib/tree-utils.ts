import type { Vec2 } from '$lib';

export function pointInPolygon(point: Vec2, coords: Vec2[]): boolean {
	const x = point.x,
		y = point.y;
	let inside = false;

	for (let i = 0, j = coords.length - 1; i < coords.length; j = i++) {
		const current = coords[i];
		const prev = coords[j];

		// Skip if either point is null or undefined
		if (!current || !prev) continue;

		const xi = current.x,
			yi = current.y;
		const xj = prev.x,
			yj = prev.y;

		const intersect = yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi + 0.000001) + xi;
		if (intersect) inside = !inside;
	}

	return inside;
}

export function generatePointsInsidePolygon(
	coords: Vec2[],
	spacing: number,
	jitter: number
): Vec2[] {
	const xs = coords.map((p) => p.x);
	const ys = coords.map((p) => p.y);
	const [minX, maxX] = [Math.min(...xs), Math.max(...xs)];
	const [minY, maxY] = [Math.min(...ys), Math.max(...ys)];

	const result: Vec2[] = [];
	for (let x = minX; x <= maxX; x += spacing) {
		for (let y = minY; y <= maxY; y += spacing) {
			const maxAttempts = 10;

			for (let attempt = 0; attempt < maxAttempts; attempt++) {
				const jitterX = (Math.random() - 0.5) * jitter;
				const jitterY = (Math.random() - 0.5) * jitter;
				const point = { x: x + jitterX, y: y + jitterY };

				if (pointInPolygon(point, coords)) {
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
