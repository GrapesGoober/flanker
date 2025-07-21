<script lang="ts">
	import { onMount } from 'svelte';
	import * as d3 from 'd3';

	let mapLayer: SVGGElement | null = null;
	let zoomLayer: SVGGElement | null = null;
	let transform: d3.ZoomTransform = d3.zoomIdentity;

	const GRID_SPACING = 100;
	const GRID_START = -200;
	const GRID_END = 1200;

	// Calculate vertical grid lines (vary x, fixed y)
	const lines: number[] = [];
	for (let i = GRID_START; i <= GRID_END; i += GRID_SPACING) {
		lines.push(i);
	}

	onMount(() => {
		const mapDiv = d3.select(mapLayer);
		const svgZoom = d3.select(zoomLayer);
		const zoom = d3
			.zoom<SVGSVGElement, unknown>()
			.scaleExtent([0.5, 10])
			.on('zoom', (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
				transform = event.transform;
				svgZoom.attr('transform', transform.toString());
			});

		mapDiv.call(zoom as any);
	});
</script>

<!-- I'm prototying behaviours at the moment, so proper structure comes later -->
<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<svg bind:this={mapLayer} class="map-box">
	<g bind:this={zoomLayer}>
		<foreignObject x="10" y="10" width="200" height="200">
			<h1>Hello</h1>
			<svg>
				<circle cx="10" cy="10" r="10" fill="red" />
			</svg>
			<svg>
				<circle cx="20" cy="20" r="10" fill="blue" />
			</svg>
		</foreignObject>
		{#each lines as i}
			<line x1={i} y1={GRID_START} x2={i} y2={GRID_END} class="grid-line" />
			<line x1={GRID_START} y1={i} x2={GRID_END} y2={i} class="grid-line" />
		{/each}
	</g>
</svg>

<style>
	.map-box {
		border: 1px solid #ccc;
		width: 100%;
		height: 90vh;
	}
	svg {
		width: 100%;
		height: 100%;
		touch-action: none; /* required for pointer-based zooming */
		background-color: #ecffc7;
	}
	.grid-line {
		stroke-width: 1;
		stroke: #00000020;
	}
</style>
