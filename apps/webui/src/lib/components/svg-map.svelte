<script lang="ts">
	import type { Vec2 } from '$lib/api';
	import * as d3 from 'd3';
	import { onMount, type Snippet } from 'svelte';

	type Props = {
		svgSnippet: Snippet;
		height?: string;
		width?: string;
		initialZoom?: number;
	};
	let {
		svgSnippet,
		height = '90vh',
		width = '100%',
		initialZoom = 2
	}: Props = $props();

	const componentId = $props.id();
	const gridPatternId = `${componentId}-grid-pattern`;

	let mapLayer: SVGSVGElement | null = null; // Handles events
	let zoomLayer: SVGGElement | null = null; // Applies zoom-pan
	let gridLayer: SVGPatternElement | null = null; // Applies zoom-pan separately
	let transform: d3.ZoomTransform = d3.zoomIdentity;

	// Convert screen coordinates to world position using current transform
	export function ToWorldCoords(coords: Vec2): Vec2 {
		const [x, y] = transform.invert([coords.x, coords.y]);
		return { x, y };
	}

	// Set up D3 pan/zoom
	onMount(() => {
		const mapDiv = d3.select(mapLayer as SVGSVGElement);
		const zoomSvg = d3.select(zoomLayer);
		const pattern = d3.select(gridLayer);
		const zoom = d3
			.zoom<SVGSVGElement, unknown>()
			.scaleExtent([0.5, 10])
			.on('zoom', (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
				transform = event.transform;
				zoomSvg.attr('transform', transform.toString());
				pattern.attr('patternTransform', transform.toString());
			});

		// Set default starting zoom and pan
		mapDiv.call(zoom.transform, d3.zoomIdentity.scale(initialZoom));
		mapDiv.call(zoom as any);
	});
</script>

<svg
	bind:this={mapLayer}
	class="map-box"
	style:height
	style:width
>
	<defs>
		<pattern
			bind:this={gridLayer}
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
		{@render svgSnippet()}
	</g>
	<rect
		class="grid-layer"
		width="100%"
		height="100%"
		fill={`url(#${gridPatternId})`}
	/>
</svg>

<style lang="less">
	.map-box {
		border: 1px solid #ccc;
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
