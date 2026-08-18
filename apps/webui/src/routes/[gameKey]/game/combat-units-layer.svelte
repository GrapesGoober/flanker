<script lang="ts">
	import type { Vec2 } from '$lib/api';
	/*
	CombatUnitsLayer Svelte component
	Renders combat units and overlays for gameplay, including selection and action markers.
	Handles unit selection and icon display based on game state.
	*/
	import {
		Arrow,
		BlankFriendlyUnit,
		BorderFriendlyUnit,
		BorderHostileUnit,
		RifleSquad
	} from '$lib/components';
	import { PlayerController } from './player-controller.svelte';

	type Props = {
		controller: PlayerController;
	};

	let { controller = $bindable() }: Props = $props();

	/* Selects a unit and updates the controller state. */
	function SelectUnit(unitId: string, event: MouseEvent) {
		if (controller.isFetching) return;
		event.stopPropagation(); // Prevent the terrain's onclick trigger
		controller.selectUnit(unitId);
	}

	function GetUnitPosition(unitId: string): Vec2 | null {
		for (let squad of controller.viewState.squads) {
			if (squad.unitId == unitId) {
				return squad.position;
			}
		}
		return null;
	}
</script>

<!-- Draw overlay for gameplay icons -->
<svg overflow="visible" class="transparent-icons">
	{#each controller.viewState.squads as unit}
		{#if unit.firingAt != null}
			{@const unitPos = GetUnitPosition(unit.firingAt[0])}
			{#if unitPos != null}
				<Arrow start={unit.position} end={unitPos} offset={10} />
			{/if}
		{/if}
	{/each}
	{#if controller.state.type !== 'default'}
		{@const selectedUnit = controller.state.selectedUnit}
		{@const position = controller.state.selectedUnit.position}

		{#if selectedUnit.isFriendly}
			<g transform="translate({position.x}, {position.y})"><BorderFriendlyUnit /></g>
		{:else if !selectedUnit.isFriendly}
			<g transform="translate({position.x}, {position.y})"><BorderHostileUnit /></g>
		{/if}
		{#if controller.state.type == 'moveMarked'}
			{@const moveMarker = controller.state.moveMarker}
			<g transform="translate({moveMarker.x}, {moveMarker.y})"><BlankFriendlyUnit /></g>
			<Arrow start={selectedUnit.position} end={controller.state.moveMarker} offset={6} />
		{:else if controller.state.type == 'attackMarked'}
			{@const targetPos = controller.state.target.position}
			<Arrow start={selectedUnit.position} end={targetPos} offset={12} />
			<g transform="translate({targetPos.x}, {targetPos.y})"><BorderHostileUnit /></g>
		{/if}
	{/if}
</svg>

<!-- Draw the combat units -->
<svg overflow="visible">
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<!-- Draw combat units -->
	{#each controller.viewState.squads as unit, index}
		<g onclick={(event) => SelectUnit(unit.unitId, event)}>
			<RifleSquad bind:rifleSquadData={controller.viewState.squads[index]} />
		</g>
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
