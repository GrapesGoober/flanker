<script lang="ts">
	/*
	Logs page Svelte component
	Displays action logs, terrain, and unit state for replay and analysis.
	Handles log navigation and map rendering.
	*/
	import { onMount } from 'svelte';
	import { SvgMap } from '$lib/components';
	import { GetLogs, GetTerrainData, type ActionLog, type TerrainModel } from '$lib/api';
	import TerrainLayer from '../../../../lib/components/terrain-layer.svelte';
	import LogViewLayer from './log-view-layer.svelte';

	let map: SvgMap | null = $state(null);
	let logData: ActionLog[] = $state([]);
	let index: number = $state(0);
	let terrain: TerrainModel[] = $state([]);
	let action: ActionLog | null = $derived(logData[index] ?? null);

	/* Loads terrain and log data on mount. */
	onMount(async () => {
		terrain = await GetTerrainData();
		logData = await GetLogs();
	});
</script>

<!-- Map and log view layers for current log index -->
{#snippet mapSvgSnippet()}
	<TerrainLayer terrainData={terrain} />
	<LogViewLayer {logData} {index}></LogViewLayer>
{/snippet}
<!-- Log index input for navigation -->
index = <input type="number" class="number-input" bind:value={index} />

<!-- Map SVG rendering -->
<div>
	<SvgMap svgSnippet={mapSvgSnippet} bind:this={map} />
</div>

<!-- Display current action log details -->
{#if action}
	{action.logType}
	{JSON.stringify(action.body)}
	{JSON.stringify(action.result)}
{/if}
