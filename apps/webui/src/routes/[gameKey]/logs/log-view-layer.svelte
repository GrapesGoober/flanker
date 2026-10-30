<script lang="ts">
	import { type ActionLogModel, type GameViewStateModel } from '$lib/api';
	import {
		BorderFriendlyUnit,
		BorderHostileUnit,
		FireOutcomeArrow,
		RifleSquad
	} from '$lib/components';

	type Props = {
		logData: ActionLogModel[];
		index: number;
	};

	let props: Props = $props();
	let currentView: GameViewStateModel = $derived(
		props.logData[props.index]?.viewState ?? {
			objectiveState: 'INCOMPLETE',
			hasInitiative: false,
			squads: []
		}
	);
	let currentAction: ActionLogModel | null = $derived(
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
				<g
					transform="translate(
						{actorUnit.position.x}, 
						{actorUnit.position.y}
					)"
				>
					{#if actorUnit.isFriendly}
						<BorderFriendlyUnit />
					{:else}
						<BorderHostileUnit />
					{/if}
				</g>

				{#if currentAction.logType == 'FireActionLogModel'}
					{@const targetUnit = currentView.squads.filter(
						(unit) => unit.unitId == currentAction.body.targetId
					)[0]}
					{#if targetUnit}
						{@const targetPos = targetUnit.position}
						<g transform="translate({targetPos.x}, {targetPos.y})">
							{#if targetUnit.isFriendly}
								<BorderFriendlyUnit />
							{:else}
								<BorderHostileUnit />
							{/if}
						</g>

						<FireOutcomeArrow
							from={actorUnit.position}
							to={targetUnit.position}
							effectLabel={currentAction.outcome ?? ''}
						/>
					{/if}
				{/if}
			{/if}
		{/if}
	</g>

	<!-- Render all squads for the current log view -->
	{#each currentView.squads as squad}
		<RifleSquad rifleSquadData={squad} />
	{/each}
</svg>

<style lang="less">
	* {
		font-size: large;
		font-family: Verdana, Geneva, Tahoma, sans-serif;
	}
	.transparent-icons {
		opacity: 0.5;
	}
</style>
