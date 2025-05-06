<script lang="ts">
	import { onMount } from 'svelte';
	import * as d3 from 'd3';
	import RifleSquad from './rifle-squad.svelte';
	import {
		GetTerrainData,
		GetRifleSquadsData,
		MoveRifleSquad,
		type RifleSquadData,
		type TerrainFeatureData,
		type Vec2
	} from '$lib';
	import TerrainFeature from './terrain-feature.svelte';

	let svgLayer: SVGSVGElement | null = $state(null);
	let zoomLayer: SVGGElement | null = $state(null);
	let transform: d3.ZoomTransform = $state(d3.zoomIdentity);
	let marker: Vec2 | null = $state(null);
	let terrainData: TerrainFeatureData[] = $state([]);
	let unitData: RifleSquadData[] = $state([]);
	let selectedUnit: number | null = $state(null);

	onMount(async () => {
		terrainData = await GetTerrainData();
		unitData = await GetRifleSquadsData();

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

	function AddMarker(event: MouseEvent) {
		if (selectedUnit === null) {
			return;
		}

		// Convert click event to world position vector
		const point = d3.pointer(event, svgLayer); // Get click coords in SVG space
		const worldPos = transform.invert(point); // Adjust for zoom/pan to world space
		marker = { x: worldPos[0], y: worldPos[1] };
	}

	async function ConfirmMarker(_: MouseEvent) {
		// Only apply marker for selected squad & existing marker
		if (selectedUnit !== null && marker !== null) {
			unitData = await MoveRifleSquad(selectedUnit, marker);
			marker = null;
		}
	}

	function SelectUnit(unit_id: number, event: MouseEvent) {
		event.stopPropagation();
		// Only select unit when no marker is active
		if (marker !== null) {
			return;
		}
		selectedUnit = unit_id;
	}
</script>

<!-- I'm prototying behaviours at the moment, so proper structure comes later -->
<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<svg
	bind:this={svgLayer}
	width="100%"
	height="90vh"
	style="border: 1px solid #ccc"
	onclick={AddMarker}
>
	<g bind:this={zoomLayer}>
		{#each terrainData as terrainFeatureData}
			<TerrainFeature featureData={terrainFeatureData} />
		{/each}

		{#each unitData as unit}
			<g onclick={(event) => SelectUnit(unit.unit_id, event)}>
				<RifleSquad position={unit.position} isSelected={selectedUnit === unit.unit_id} />
			</g>
		{/each}

		{#if marker}
			<g onclick={ConfirmMarker}>
				<circle cx={marker.x} cy={marker.y} r="10" fill="red" />
			</g>
		{/if}
	</g>
</svg>

<style>
	svg {
		touch-action: none; /* required for pointer-based zooming */
		background-color: #fefae0;
	}
</style>
