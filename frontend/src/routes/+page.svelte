<script lang="ts">
	import { onMount } from 'svelte';
	import {
		GetTerrainData,
		GetUnitStatesData,
		MoveRifleSquad,
		type TerrainFeatureData,
		type UnitStateData,
		type Vec2
	} from '$lib';
	import RifleSquad from '$lib/rifle-squad.svelte';
	import TerrainFeature from '$lib/terrain-feature.svelte';
	import SvgMap from '$lib/svg-map.svelte';

	let marker: Vec2 | null = $state(null);
	let terrainData: TerrainFeatureData[] = $state([]);
	let unitData: UnitStateData = $state({ hasInitiative: false, squads: [] });
	let selectedUnit: number | null = $state(null);

	onMount(async () => {
		terrainData = await GetTerrainData();
		unitData = await GetUnitStatesData();
	});

	function AddMarker(event: MouseEvent, worldPos: Vec2) {
		if (selectedUnit === null) {
			return;
		}
		marker = worldPos;
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
{#snippet mapMarkup()}
	{#each terrainData as terrainFeatureData}
		<TerrainFeature featureData={terrainFeatureData} />
	{/each}

	{#each unitData.squads as unit, index}
		<g onclick={(event) => SelectUnit(unit.unitId, event)}>
			<RifleSquad bind:rifleSquadData={unitData.squads[index]} />
		</g>
	{/each}

	{#if marker}
		<g onclick={ConfirmMarker}>
			<circle cx={marker.x} cy={marker.y} r="10" fill="red" />
		</g>
	{/if}
{/snippet}

<SvgMap onclick={AddMarker} body={mapMarkup} />
