<script lang="ts">
	import { onMount } from 'svelte';
	import * as d3 from 'd3';
	import RifleSquad from './rifle-squad.svelte';
	import { GetTerrainData, GetRifleSquadsData, type RifleSquadData, type TerrainFeatureData } from '$lib';
	import TerrainFeature from './terrain-feature.svelte';

	let svgLayer: SVGSVGElement | null = $state(null);
	let zoomLayer: SVGGElement | null = $state(null);
	let transform: d3.ZoomTransform = $state(d3.zoomIdentity);
	let markers: [number, number][] = $state([]);
	let terrainData: TerrainFeatureData[] = $state([]);
	let unitData: RifleSquadData[] = $state([]);

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
		const point = d3.pointer(event, svgLayer); // Get click coords in SVG space
		const inverted = transform.invert(point); // Adjust for zoom/pan
		markers.push(inverted);
		PrettyPrintMarkers();
	}

	function PrettyPrintMarkers() {
		const pythonSyntax = markers.map(([x, y]) => `Vec2(${Math.round(x)}, ${Math.round(y)})`).join(', ');
		console.log(`[${pythonSyntax}]`);
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
			<RifleSquad position={unit.position} />
		{/each}

		{#each markers as [x, y]}
			<circle cx={x} cy={y} r="10" fill="red" />
		{/each}
	</g>
</svg>

<style>
	svg {
		touch-action: none; /* required for pointer-based zooming */
		background-color: #e7d5b7;
	}
</style>
