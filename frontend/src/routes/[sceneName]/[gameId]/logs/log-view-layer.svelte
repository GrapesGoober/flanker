<script lang="ts">
	import { onMount } from 'svelte';
	import { RifleSquad, BorderFriendlyUnit, Arrow, BorderHostileUnit } from '$lib/components';
	import { GetLogs, type ActionLog, type CombatUnitsViewState } from '$lib/api';

	type Props = {
		logData: ActionLog[];
		index: number;
	};

	let props: Props = $props();
	let currentView: CombatUnitsViewState = $derived(
		props.logData[props.index]?.unitState ?? {
			objectiveState: 'INCOMPLETE',
			hasInitiative: false,
			squads: []
		}
	);
	let currentAction: ActionLog | null = $derived(props.logData[props.index] ?? null);

	onMount(async () => {
		props.logData = await GetLogs();
	});
</script>

<g class="transparent-icons">
	{#if currentAction}
		{@const actorUnit = currentView.squads.filter(
			(unit) => unit.unitId == currentAction.body.unitId
		)[0]}
		{#if actorUnit}
			<g transform="translate({actorUnit.position.x}, {actorUnit.position.y})"
				><BorderFriendlyUnit /></g
			>
			{#if currentAction.logType == 'FireActionLog' || currentAction.logType == 'AssaultActionLog'}
				{@const targetUnit = currentView.squads.filter(
					(unit) => unit.unitId == currentAction.body.targetId
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

<style lang="less">
	.transparent-icons {
		opacity: 0.5;
	}
</style>
