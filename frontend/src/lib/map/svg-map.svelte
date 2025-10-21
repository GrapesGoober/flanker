<script lang="ts">
	import { onMount, type Snippet } from 'svelte';
	import * as d3 from 'd3';
	import type { Vec2 } from '$lib';

	type Props = {
		svgSnippet: Snippet;
	};
	let props: Props = $props();

	const gridPatternId = `grid-pattern`;
	const gridSize = 100;

	let mapLayer: SVGSVGElement | null = null;
	let zoomLayer: SVGGElement | null = null;
	let gridPattern: SVGPatternElement | null = null;
	let transform: d3.ZoomTransform = d3.zoomIdentity;

	// Convert screen coordinates to world position using current transform
	export function ToWorldCoords(coords: Vec2): Vec2 {
		const [x, y] = transform.invert([coords.x, coords.y]);
		return { x, y };
	}

	// Set up D3 pan/zoom
	onMount(() => {
		const mapDiv = d3.select(mapLayer as SVGSVGElement);
		const svgZoom = d3.select(zoomLayer);
		const pattern = d3.select(gridPattern);
		const zoom = d3
			.zoom<SVGSVGElement, unknown>()
			.scaleExtent([0.5, 10])
			.on('zoom', (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
				transform = event.transform;
				svgZoom.attr('transform', transform.toString());
				// Update grid pattern so it zooms and pans along
				pattern.attr(
					'patternTransform',
					`translate(${transform.x},${transform.y}) scale(${transform.k})`
				);
			});

		// Set default starting zoom and pan
		mapDiv.call(zoom.transform, d3.zoomIdentity.scale(1.5));
		mapDiv.call(zoom as any);
	});
</script>

<svg bind:this={mapLayer} class="map-box">
	<defs>
		<pattern
			bind:this={gridPattern}
			id={gridPatternId}
			width={gridSize}
			height={gridSize}
			patternUnits="userSpaceOnUse"
		>
			<path class="map-grid-line" d="M {gridSize} 0 L 0 0 0 {gridSize}" fill="none" />
		</pattern>
	</defs>
	<g bind:this={zoomLayer}>
		{@render props.svgSnippet()}
	</g>
	<rect width="100%" height="100%" fill={`url(#${gridPatternId})`} />
</svg>

<style lang="less">
	@stroke-width: 1.5;
	@road-width: 5;
	.map-box {
		border: 1px solid #ccc;
		width: 100%;
		height: 90vh;
		touch-action: none; /* required for pointer-based zooming */
		background-color: #ecffc7;
	}
	.map-grid-line {
		stroke-width: 2;
		stroke: #00000020;
		pointer-events: none;
	}
</style>
