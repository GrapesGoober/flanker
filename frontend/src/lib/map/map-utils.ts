import type { Vec2 } from '$lib';
import * as d3 from 'd3';

export function GetClosedPath(coords: Vec2[]): string {
	const line = d3
		.line<Vec2>()
		.x((d) => d.x)
		.y((d) => d.y)
		.curve(d3.curveCardinalClosed.tension(1));
	return line(coords) || '';
}

export function GetSmoothedClosedPath(coords: Vec2[], tension: number): string {
	const line = d3
		.line<Vec2>()
		.x((d) => d.x)
		.y((d) => d.y)
		.curve(d3.curveCardinalClosed.tension(tension));
	return line(coords) || '';
}

export function GetSmoothedPath(coords: Vec2[], tension: number): string {
	const line = d3
		.line<Vec2>()
		.x((d) => d.x)
		.y((d) => d.y)
		.curve(d3.curveCardinal.tension(tension));
	return line(coords) || '';
}

export function SetupZoomPan(
	mapLayer: SVGSVGElement,
	zoomLayer: SVGGElement,
	transform: d3.ZoomTransform
) {
	const mapDiv = d3.select(mapLayer as SVGSVGElement);
	const svgZoom = d3.select(zoomLayer);
	const zoom = d3
		.zoom<SVGSVGElement, unknown>()
		.scaleExtent([0.5, 10])
		.on('zoom', (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
			transform = event.transform;
			svgZoom.attr('transform', transform.toString());
		});

	// Set default starting zoom and pan
	mapDiv.call(zoom.transform, d3.zoomIdentity.scale(1.5));

	mapDiv.call(zoom as any);
}

export function GetGridLines(bounds: {
	xMin: number;
	xMax: number;
	yMin: number;
	yMax: number;
}): [Vec2, Vec2][] {
	const GRID_SPACING = 100;
	const lines: [Vec2, Vec2][] = [];

	// Horizontal lines (y varies)
	for (let y = bounds.yMin; y <= bounds.yMax; y += GRID_SPACING) {
		lines.push([
			{ x: bounds.xMin, y },
			{ x: bounds.xMax, y }
		]);
	}

	// Vertical lines (x varies)
	for (let x = bounds.xMin; x <= bounds.xMax; x += GRID_SPACING) {
		lines.push([
			{ x, y: bounds.yMin },
			{ x, y: bounds.yMax }
		]);
	}

	return lines;
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
