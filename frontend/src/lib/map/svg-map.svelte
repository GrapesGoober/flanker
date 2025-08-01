<script lang="ts">
	import { onMount, type Snippet } from 'svelte';
	import * as d3 from 'd3';
	import type { Vec2 } from '$lib';
	import { GetGridLines } from './map-utils';

	type Props = {
		svgSnippet: Snippet;
	};
	let props: Props = $props();

	let mapLayer: SVGSVGElement | null = null;
	let zoomLayer: SVGGElement | null = null;
	let transform: d3.ZoomTransform = d3.zoomIdentity;
	const lines: [Vec2, Vec2][] = GetGridLines({
		xMin: 0,
		xMax: 500,
		yMin: 0,
		yMax: 500
	});

	// Convert screen coordinates to world position using current transform
	export function ToWorldCoords(coords: Vec2): Vec2 {
		const [x, y] = transform.invert([coords.x, coords.y]);
		return { x, y };
	}

	// Set up D3 pan/zoom
	onMount(() => {
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
	});
</script>

<svg bind:this={mapLayer} class="map-box">
	<g bind:this={zoomLayer}>
		{@render props.svgSnippet()}

		<!-- Translucent grid lines on top of everything -->
		{#each lines as [start, end]}
			<line x1={start.x} y1={start.y} x2={end.x} y2={end.y} class="map-grid-line" />
		{/each}
	</g>
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
		stroke-width: 1;
		stroke: #00000020;
		pointer-events: none;
	}
</style>
