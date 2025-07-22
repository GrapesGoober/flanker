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
	import Arrow from '$lib/svg-icons/arrow.svelte';

	let map: SvgMap | null = $state(null);
	let marker: Vec2 | null = $state(null);
	let terrainData: TerrainFeatureData[] = $state([]);
	let unitData: CombatUnitsData = $state({ hasInitiative: false, squads: [] });
	let selectedUnitId: number | null = $state(null);
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
			unitData = await MoveRifleSquad(selectedUnitId, marker);
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
		selectedUnitId = unit_id;
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
		<g onclick={ConfirmMarker} fill-opacity="0.5">
			<circle cx={marker.x} cy={marker.y} r="5" fill="red" />
			<Arrow start={{ x: 0, y: 0 }} end={marker} />
		</g>
	{/if}
{/snippet}

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div bind:this={clickTarget} onclick={AddMarker}>
	<SvgMap svgSnippet={mapSvgSnippet} {terrainData} bind:this={map} />
</div>
