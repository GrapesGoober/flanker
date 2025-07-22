<script lang="ts">
	import { onMount } from 'svelte';
	import {
		GetTerrainData,
		GetUnitStatesData,
		MoveRifleSquad,
		type TerrainFeatureData,
		type CombatUnitsData,
		type Vec2
	} from '$lib';
	import RifleSquad from '$lib/rifle-squad.svelte';
	import SvgMap from '$lib/map/svg-map.svelte';

	let map: SvgMap | null = $state(null);
	let marker: Vec2 | null = $state(null);
	let terrainData: TerrainFeatureData[] = $state([]);
	let unitData: CombatUnitsData = $state({ hasInitiative: false, squads: [] });
	let selectedUnit: number | null = $state(null);

	onMount(async () => {
		terrainData = await GetTerrainData();
		unitData = await GetUnitStatesData();
	});

	function AddMarker(event: MouseEvent) {
		if (map == null) {
			return;
		}
		if (unitData.hasInitiative === false) {
			return;
		}

		if (selectedUnit === null) {
			return;
		}

		marker = map.ToWorldCoords({ x: event.clientX, y: event.clientY });
	}

	async function ConfirmMarker(_: MouseEvent) {
		if (unitData.hasInitiative === false) {
			return;
		}
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
		// Deselect all units, then select the correct one
		for (const unit of unitData.squads) {
			unit.isSelected = unit.unitId === unit_id;
		}
		selectedUnit = unit_id;
	}
</script>

<!-- I'm prototying behaviours at the moment, so proper structure comes later -->
<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
{#snippet mapSvgSnippet()}
	{#each unitData.squads as unit, index}
		{#if unitData.squads[index]}
			<g onclick={(event) => SelectUnit(unit.unitId, event)}>
				<RifleSquad bind:rifleSquadData={unitData.squads[index]} />
			</g>
		{/if}
	{/each}

	{#if marker}
		<g onclick={ConfirmMarker}>
			<circle cx={marker.x} cy={marker.y} r="10" fill="red" />
		</g>
	{/if}
{/snippet}

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div onclick={AddMarker}>
	<SvgMap svgSnippet={mapSvgSnippet} {terrainData} bind:this={map} />
</div>
