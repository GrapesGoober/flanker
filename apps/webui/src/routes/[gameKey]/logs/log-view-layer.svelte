<script lang="ts">
	import { type ActionLog, type GameViewState } from '$lib/api';
	import {
		BorderFriendlyUnit,
		BorderHostileUnit,
		FireEffectArrows,
		RifleSquad
	} from '$lib/components';

	type Props = {
		logData: ActionLog[];
		index: number;
	};

	let props: Props = $props();
	let currentView: GameViewState = $derived(
		props.logData[props.index]?.viewState ?? {
			objectiveState: 'INCOMPLETE',
			hasInitiative: false,
			squads: [],
			fireEffectPairs: []
		}
	);
	let currentAction: ActionLog | null = $derived(
		props.logData[props.index] ?? null
	);
</script>

<svg overflow="visible">
	<!-- Overlay for action icons and arrows -->
	<g class="transparent-icons">
		{#each currentView.fireEffectPairs as fireEffect}
			<FireEffectArrows
				positionA={fireEffect.positionA}
				positionB={fireEffect.positionB}
				fireEffectA={fireEffect.fireEffectA}
				fireEffectB={fireEffect.fireEffectB}
			/>
		{/each}

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

				{#if currentAction.logType == 'FireActionLog'}
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
