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

	function OnMapClick(event: MouseEvent) {
		// Convert click event to world position vector
		const point = d3.pointer(event, svgLayer); // Get click coords in SVG space
		const inverted = transform.invert(point); // Adjust for zoom/pan to world space
		const worldPos: Vec2 = { x: inverted[0], y: inverted[1] };

		ApplyMarker(worldPos);
	}

	async function ApplyMarker(worldPos: Vec2) {
		// Only add a new marker for selected squad
		if (selectedUnit === null) {
			return;
		}

		// Only add a new marker when existing one doesn't exist
		if (marker == null) {
			marker = worldPos;
			return;
		}
		// If existing one exists, interpret the click as either
		// - confirming the marker if clicked close enough (bounding box)
		// - or, cancelling the marker if clicked too far
		const distance = Math.abs(worldPos.x - marker.x) + Math.abs(worldPos.y - marker.y);
		const threshold = 10;
		// Cancelling marker
		if (distance >= threshold) {
			marker = null;
		}
		// Confirming marker. Mutate the unit data
		else {
			unitData = await MoveRifleSquad(selectedUnit, marker);
		}
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
	onclick={OnMapClick}
>
	<g bind:this={zoomLayer}>
		{#each terrainData as terrainFeatureData}
			<TerrainFeature featureData={terrainFeatureData} />
		{/each}

		{#each unitData as unit}
			<g onclick={() => (selectedUnit = unit.unit_id)}>
				<RifleSquad position={unit.position} isSelected={selectedUnit === unit.unit_id} />
			</g>
		{/each}

		{#if marker}
			<circle cx={marker.x} cy={marker.y} r="10" fill="red" />
		{/if}
	</g>
</svg>

<style>
	svg {
		touch-action: none; /* required for pointer-based zooming */
		background-color: #fefae0;
	}
</style>
