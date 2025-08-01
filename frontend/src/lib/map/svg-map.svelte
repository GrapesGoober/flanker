<script lang="ts">
	import { onMount, type Snippet } from 'svelte';
	import * as d3 from 'd3';
	import type { TerrainFeatureData, Vec2 } from '$lib';
	import TreeTriangle from '../svg-icons/tree-triangle.svelte';
	import {
		GetClosedPath,
		GetGridLines,
		GetSmoothedClosedPath,
		GetSmoothedPath,
		generatePointsInsidePolygon
	} from './map-utils';

	type Props = {
		terrainData: TerrainFeatureData[];
		svgSnippet: Snippet;
	};
	let props: Props = $props();

	let mapLayer: SVGSVGElement | null = null;
	let zoomLayer: SVGGElement | null = null;
	let transform: d3.ZoomTransform = d3.zoomIdentity;
	const lines: [Vec2, Vec2][] = GetGridLines({
		xMin: -200,
		xMax: 1000,
		yMin: -200,
		yMax: 1000
	});

	// Road's boarders need to be drawn separately
	function FilterRoads(): TerrainFeatureData[] {
		return props.terrainData.filter((feature) => feature.terrainType === 'ROAD');
	}

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
		<!-- Road's boarders need to be drawn separately -->
		{#each FilterRoads() as road}
			<path d={GetSmoothedPath(road.coordinates, 0.7)} class="terrain-road-border" />
		{/each}

		<!-- Draw each polygons -->
		{#each props.terrainData as terrain}
			{#if terrain.terrainType == 'FOREST'}
				<!-- Forest has separate dashed border (so that it rests inside) -->
				<path d={GetSmoothedClosedPath(terrain.coordinates, 0.7)} class="forest" />
				<path d={GetSmoothedClosedPath(terrain.coordinates, 0.7)} class="forest-border" />
				{#each generatePointsInsidePolygon(terrain.coordinates, 20, 15) as p}
					<g transform="translate({p.x}, {p.y})">
						<TreeTriangle />
					</g>
				{/each}
			{:else if terrain.terrainType == 'FIELD'}
				<path d={GetSmoothedClosedPath(terrain.coordinates, 0.7)} class="field" />
			{:else if terrain.terrainType == 'WATER'}
				<path d={GetSmoothedClosedPath(terrain.coordinates, 0.7)} class="water" />
			{:else if terrain.terrainType == 'BUILDING'}
				<path d={GetClosedPath(terrain.coordinates)} class="building" />
			{:else if terrain.terrainType == 'ROAD'}
				<path d={GetSmoothedPath(terrain.coordinates, 0.7)} class="terrain-road" />
			{/if}
		{/each}

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
	.terrain-road-border {
		fill: none;
		stroke: #d0dcb8;
		stroke-width: @road-width + @stroke-width * 2;
	}
	.terrain-road {
		fill: none;
		stroke: #eff6e0;
		stroke-width: @road-width;
	}
	.forest {
		fill: #c1da91;
		stroke: #c1da91;
		stroke-width: @stroke-width;
	}
	.forest-border {
		fill: none;
		stroke: #a2bf69;
		stroke-width: @stroke-width;
		stroke-dasharray: 8, 8;
	}
	.water {
		fill: #a5dac6;
		stroke: #a5dac6;
		stroke-width: @stroke-width;
	}
	.field {
		fill: #f5c887aa;
		stroke: #cba57aaa;
		stroke-width: @stroke-width;
	}
	.building {
		fill: #aaa;
		stroke: #999;
		stroke-width: @stroke-width;
		stroke-linecap: square;
	}
</style>
