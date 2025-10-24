<script lang="ts">
	import { onMount } from 'svelte';
	import { SvgMap } from '$lib/components';
	import {
		GetLogs,
		GetTerrainData,
		type ActionLog,
		type CombatUnitsViewState,
		type TerrainModel
	} from '$lib/api';
	import TerrainLayer from '../../../../lib/components/terrain-layer.svelte';
	import LogViewLayer from './log-view-layer.svelte';

	let map: SvgMap | null = $state(null);
	let logData: ActionLog[] = $state([]);
	let index: number = $state(0);
	let terrain: TerrainModel[] = $state([]);
	let currentView: CombatUnitsViewState = $derived(
		logData[index]?.unitState ?? {
			objectiveState: 'INCOMPLETE',
			hasInitiative: false,
			squads: []
		}
	);
	let action: ActionLog | null = $derived(logData[index] ?? null);

	onMount(async () => {
		terrain = await GetTerrainData();
		logData = await GetLogs();
	});
</script>

{#snippet mapSvgSnippet()}
	<TerrainLayer terrainData={terrain} />
	<LogViewLayer {logData} {index}></LogViewLayer>
{/snippet}
index = <input type="number" class="number-input" bind:value={index} />

<div>
	<SvgMap svgSnippet={mapSvgSnippet} bind:this={map} />
</div>

{#if action}
	{action.logType}
	{JSON.stringify(action.body)}
	{JSON.stringify(action.result)}
{/if}
