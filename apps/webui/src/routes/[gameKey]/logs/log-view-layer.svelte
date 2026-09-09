<script lang="ts">
	import { type ActionLog, type GameViewState } from '$lib/api';
	import {
		BorderFriendlyUnit,
		BorderHostileUnit,
		RifleSquad
	} from '$lib/components';
	import UiMarkerArrows from '$lib/components/svg-icons/ui-marker-arrows.svelte';

	type Props = {
		logData: ActionLog[];
		index: number;
	};

	let props: Props = $props();
	let currentView: GameViewState = $derived(
		props.logData[props.index]?.viewState ?? {
			objectiveState: 'INCOMPLETE',
			hasInitiative: false,
			squads: []
		}
	);
	let currentAction: ActionLog | null = $derived(
		props.logData[props.index] ?? null
	);
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
						<UiMarkerArrows
							start={actorUnit.position}
							end={targetPos}
							headOffset={10}
						/>
						<g transform="translate({targetPos.x}, {targetPos.y})"
							><BorderHostileUnit /></g
						>
					{/if}
				{/if}
			{/if}
		{/if}
	</g>

	<!-- Render all squads for the current log view -->
	{#each currentView.squads as _, index}
		<RifleSquad bind:rifleSquadData={currentView.squads[index]} />
	{/each}
</svg>

<style lang="less">
	.transparent-icons {
		opacity: 0.5;
	}
</style>
