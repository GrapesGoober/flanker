<script lang="ts">
	import { onMount } from 'svelte';
	import SvgMap from '$lib/map/svg-map.svelte';
	import {
		GetLogs,
		GetTerrainData,
		type ActionLog,
		type CombatUnitsViewState,
		type TerrainFeatureData
	} from '$lib';
	import TerrainFeatures from '../terrain-features.svelte';
	import LogviewCombatUnits from './logview-combat-units.svelte';

	let map: SvgMap | null = $state(null);
	let logData: ActionLog[] = $state([]);
	let index: number = $state(0);
	let terrain: TerrainFeatureData[] = $state([]);
	let currentView: CombatUnitsViewState = $derived(
		logData[index]?.unitState ?? {
			objectivesState: 'INCOMPLETE',
			hasInitiative: false,
			squads: []
		}
	);

	onMount(async () => {
		terrain = await GetTerrainData();
		logData = await GetLogs();
	});
</script>

{#snippet mapSvgSnippet()}
	<TerrainFeatures terrainData={terrain} />
	<LogviewCombatUnits bind:unitData={currentView} />
{/snippet}
index = <input type="number" class="number-input" bind:value={index} />

<div>
	<SvgMap svgSnippet={mapSvgSnippet} bind:this={map} />
</div>
