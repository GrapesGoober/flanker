<script lang="ts">
	/*
	LogViewLayer Svelte component
	Renders unit icons and action overlays for a specific log entry.
	Handles display of actor and target units for fire/assault actions.
	*/
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

	/* Loads log data on mount. */
	onMount(async () => {
		props.logData = await GetLogs();
	});
</script>

<svg overflow="visible">
	<!-- Overlay for action icons and arrows -->
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

	<!-- Render all squads for the current log view -->
	{#each currentView.squads as unit, index}
		<RifleSquad bind:rifleSquadData={currentView.squads[index]} />
	{/each}
</svg>

<style lang="less">
	.transparent-icons {
		opacity: 0.5;
	}
</style>
