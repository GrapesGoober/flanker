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
	import RifleSquad from '$lib/rifle-squad.svelte';
	import BorderFriendlyUnit from '$lib/svg-icons/border-friendly-unit.svelte';
	import Arrow from '$lib/svg-icons/arrow.svelte';
	import BlankUnit from '$lib/svg-icons/blank-friendly-unit.svelte';
	import BorderHostileUnit from '$lib/svg-icons/border-hostile-unit.svelte';

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
	let action: ActionLog | null = $derived(logData[index] ?? null);

	onMount(async () => {
		terrain = await GetTerrainData();
		logData = await GetLogs();
	});
</script>

{#snippet mapSvgSnippet()}
	<TerrainFeatures terrainData={terrain} />

	<g class="transparent-icons">
		{#if action}
			{@const actorUnit = currentView.squads.filter((unit) => unit.unitId == action.body.unitId)[0]}
			{#if actorUnit}
				<g transform="translate({actorUnit.position.x}, {actorUnit.position.y})"
					><BorderFriendlyUnit /></g
				>
				{#if action.type == 'fire' || action.type == 'assault'}
					{@const targetUnit = currentView.squads.filter(
						(unit) => unit.unitId == action.body.targetId
					)[0]}
					{#if targetUnit}
						{@const targetPos = targetUnit.position}
						<Arrow start={actorUnit.position} end={targetPos} offset={12} />
						<g transform="translate({targetPos.x}, {targetPos.y})"><BorderHostileUnit /></g>
					{/if}
				{/if}
			{/if}
		{/if}
	</g>

	{#each currentView.squads as unit, index}
		<RifleSquad bind:rifleSquadData={currentView.squads[index]} />
	{/each}
{/snippet}
index = <input type="number" class="number-input" bind:value={index} />

<div>
	<SvgMap svgSnippet={mapSvgSnippet} bind:this={map} />
</div>

{#if action}
	{action.type}
	{JSON.stringify(action.body)}
	{JSON.stringify(action.result)}
{/if}

<style lang="less">
	.transparent-icons {
		opacity: 0.5;
	}
</style>
