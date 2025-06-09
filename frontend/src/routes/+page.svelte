<script lang="ts">
	import { onMount } from 'svelte';
	import * as d3 from 'd3';
	import {
		GetTerrainData,
		GetRifleSquadsData,
		MoveRifleSquad,
		type RifleSquadData,
		type TerrainFeatureData,
		type Vec2
	} from '$lib';
	import Map from '$lib/map.svelte';

	type MapProps = {
		terrainData: TerrainFeatureData[];
		unitData: RifleSquadData[];
	};

	let mapProps: MapProps = $state({
		terrainData: [],
		unitData: []
	});

	let svgLayer: SVGSVGElement | null = $state(null);
	let zoomLayer: SVGGElement | null = $state(null);
	let transform: d3.ZoomTransform = $state(d3.zoomIdentity);
	let marker: Vec2 | null = $state(null);
	let selectedUnit: number | null = $state(null);

	onMount(async () => {
		mapProps.terrainData = await GetTerrainData();
		mapProps.unitData = await GetRifleSquadsData();

		const svg = d3.select(svgLayer);
		const g = d3.select(zoomLayer);
		const zoom = d3
			.zoom<SVGSVGElement, unknown>()
			.scaleExtent([0.5, 10])
			.on('zoom', (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
				transform = event.transform;
				g.attr('transform', transform.toString());
			});

		svg.call(zoom as any);
	});
</script>

<Map bind:props={mapProps}></Map>
