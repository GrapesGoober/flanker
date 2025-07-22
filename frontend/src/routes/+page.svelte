<script lang="ts">
	import { onMount } from 'svelte';
	import {
		GetTerrainData,
		GetUnitStatesData,
		MoveRifleSquad,
		type TerrainFeatureData,
		type CombatUnitsData,
		type Vec2,
		type RifleSquadData
	} from '$lib';
	import RifleSquad from '$lib/rifle-squad.svelte';
	import SvgMap from '$lib/map/svg-map.svelte';
	import Arrow from '$lib/svg-icons/arrow.svelte';

	let map: SvgMap | null = $state(null);
	let marker: Vec2 | null = $state(null);
	let terrainData: TerrainFeatureData[] = $state([]);
	let unitData: CombatUnitsData = $state({ hasInitiative: false, squads: [] });
	let selectedUnitId: RifleSquadData | null = $state(null);
	let clickTarget: HTMLElement | null = $state(null);

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

		if (selectedUnitId === null) {
			return;
		}

		let node = clickTarget as HTMLElement;
		let rect = node.getBoundingClientRect();
		let x = event.clientX - rect.x; //x position within the element.
		let y = event.clientY - rect.y; //y position within the element.
		marker = map.ToWorldCoords({ x, y });
	}

	async function ConfirmMarker(_: MouseEvent) {
		if (unitData.hasInitiative === false) {
			return;
		}
		// Only apply marker for selected squad & existing marker
		if (selectedUnitId !== null && marker !== null) {
			unitData = await MoveRifleSquad(selectedUnitId.unitId, marker);
			marker = null;
		}
	}

	function SelectUnit(unitId: number, event: MouseEvent) {
		event.stopPropagation();
		// Only select unit when no marker is active
		if (marker !== null) {
			return;
		}
		// Deselect all units, then select the correct one
		for (const unit of unitData.squads) {
			unit.isSelected = unit.unitId === unitId;
			if (unit.unitId == unitId) {
				selectedUnitId = unit;
			}
		}
	}
</script>

<!-- I'm prototying behaviours at the moment, so proper structure comes later -->
<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
{#snippet mapSvgSnippet()}
	{#if marker && selectedUnitId}
		<g onclick={ConfirmMarker} fill-opacity="0.5">
			<circle cx={marker.x} cy={marker.y} r="5" fill="red" />
			<Arrow start={selectedUnitId.position} end={marker} />
		</g>
	{/if}

	{#each unitData.squads as unit, index}
		{#if unitData.squads[index]}
			<g onclick={(event) => SelectUnit(unit.unitId, event)}>
				<RifleSquad bind:rifleSquadData={unitData.squads[index]} />
			</g>
		{/if}
	{/each}
{/snippet}

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div bind:this={clickTarget} onclick={AddMarker}>
	<SvgMap svgSnippet={mapSvgSnippet} {terrainData} bind:this={map} />
</div>
