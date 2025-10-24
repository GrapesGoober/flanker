<script lang="ts">
	import { onMount } from 'svelte';
	import {
		SvgMap,
		RifleSquad,
		BorderFriendlyUnit,
		Arrow,
		BorderHostileUnit
	} from '$lib/components';
	import {
		GetLogs,
		GetTerrainData,
		type ActionLog,
		type CombatUnitsViewState,
		type TerrainModel
	} from '$lib/api';
	import TerrainFeatures from '../game/terrain-features.svelte';

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
	<TerrainFeatures terrainData={terrain} />

	<g class="transparent-icons">
		{#if action}
			{@const actorUnit = currentView.squads.filter((unit) => unit.unitId == action.body.unitId)[0]}
			{#if actorUnit}
				<g transform="translate({actorUnit.position.x}, {actorUnit.position.y})"
					><BorderFriendlyUnit /></g
				>
				{#if action.logType == 'FireActionLog' || action.logType == 'AssaultActionLog'}
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
	{action.logType}
	{JSON.stringify(action.body)}
	{JSON.stringify(action.result)}
{/if}

<style lang="less">
	.transparent-icons {
		opacity: 0.5;
	}
</style>
