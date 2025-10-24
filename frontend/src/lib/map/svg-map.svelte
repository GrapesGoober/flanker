<script lang="ts">
	import { onMount, type Snippet } from 'svelte';
	import * as d3 from 'd3';
	import type { Vec2 } from '$lib';

	type Props = {
		svgSnippet: Snippet;
	};
	let props: Props = $props();

	const gridPatternId = `grid-pattern`;

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
			width="100"
			height="100"
			patternUnits="userSpaceOnUse"
		>
			<path class="major-grid-line" d="M100,0 L0,0 0,100" fill="none" />
			<path class="minor-grid-line" d="M33,0 L33,100" fill="none" />
			<path class="minor-grid-line" d="M0,033 L100,33" fill="none" />
			<path class="minor-grid-line" d="M66,0 L66,100" fill="none" />
			<path class="minor-grid-line" d="M0,66 L100,66" fill="none" />
		</pattern>
	</defs>
	<g bind:this={zoomLayer}>
		{@render props.svgSnippet()}
	</g>
	<rect class="grid-layer" width="100%" height="100%" fill={`url(#${gridPatternId})`} />
</svg>

<style lang="less">
	.map-box {
		border: 1px solid #ccc;
		width: 100%;
		height: 90vh;
		touch-action: none; /* required for pointer-based zooming */
		background-color: #f4f2f2;
	}
	.major-grid-line {
		stroke-width: 2;
		stroke: #00000020;
		pointer-events: none;
	}

	.minor-grid-line {
		stroke-width: 0.5;
		stroke: #00000015;
		pointer-events: none;
	}
	.grid-layer {
		pointer-events: none;
	}
</style>
