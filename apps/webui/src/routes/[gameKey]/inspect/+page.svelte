<script lang="ts">
	/*
	Logs page Svelte component
	Displays action logs, terrain, and unit state for replay and analysis.
	Handles log navigation and map rendering.
	*/
	import { page } from '$app/state';
	import {
		GetMapData,
		GetStatesInspectionData,
		type GameStateInspection,
		type MapViewState,
		type Vec2
	} from '$lib/api';
	import { SvgMap, TerrainLayer } from '$lib/components';
	import { loadGameLocal } from '$lib/scenes-storage';
	import { onMount } from 'svelte';
	import InspectLayer from './inspect-layer.svelte';

	let map: SvgMap | null = $state(null);
	let clickTarget: HTMLElement | null = $state(null);

	let mapData: MapViewState = $state({
		terrains: [],
		boundary: []
	});

	let inspectionData: GameStateInspection = $state({
		viewState: {
			objectiveState: 'INCOMPLETE',
			hasInitiative: false,
			squads: []
		},
		losPolygons: [],
		moveCandidates: []
	});

	let drawFov: boolean = $state(true);
	let drawMoveCandidates: boolean = $state(true);
	let drawUnitTexts: boolean = $state(true);

	/* Loads terrain and log data on mount. */
	onMount(async () => {
		const gameKey: string = page.params['gameKey'] as string;
		const gameStateJson = loadGameLocal(gameKey);
		mapData = await GetMapData(gameStateJson);
		inspectionData = await GetStatesInspectionData(gameStateJson);
	});

	let positionMarkers: Vec2[] = $state([]);

	/** Handles click as adding a vertex or waypoint, depending on state. */
	function placeMarker(event: MouseEvent) {
		if (map == null) return;
		const node = clickTarget as HTMLElement;
		const rect = node.getBoundingClientRect();
		const x = event.clientX - rect.x;
		const y = event.clientY - rect.y;
		let worldPos = map.ToWorldCoords({ x, y });
		positionMarkers.push(worldPos);
	}
</script>

{#snippet mapSvgSnippet()}
	<TerrainLayer {mapData} />
	<InspectLayer
		{inspectionData}
		bind:drawFov
		bind:drawMoveCandidates
		bind:drawUnitTexts
		bind:positionMarkers
	/>
{/snippet}

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div onclick={placeMarker} bind:this={clickTarget}>
	<SvgMap svgSnippet={mapSvgSnippet} bind:this={map} />
</div>
<input type="checkbox" bind:checked={drawFov} />
Draw LOS Polygon as FOV <br />
<input type="checkbox" bind:checked={drawMoveCandidates} />
Draw Move Candidates <br />
<input type="checkbox" bind:checked={drawUnitTexts} />
Draw Unit Texts <br />
