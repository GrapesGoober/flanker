<script lang="ts">
	import { onMount } from 'svelte';
	import RifleSquad from '$lib/rifle-squad.svelte';
	import SvgMap from '$lib/map/svg-map.svelte';
	import Arrow from '$lib/svg-icons/arrow.svelte';
	import { PlayerController } from './player-controller.svelte';

	let map: SvgMap | null = $state(null);
	let clickTarget: HTMLElement | null = $state(null);
	let controller: PlayerController = $state(new PlayerController());

	onMount(async () => {
		await controller.initializeAsync();
	});

	function AddMarker(event: MouseEvent) {
		if (map == null) return;
		const node = clickTarget as HTMLElement;
		const rect = node.getBoundingClientRect();
		const x = event.clientX - rect.x;
		const y = event.clientY - rect.y;
		controller.setMoveMarker(map.ToWorldCoords({ x, y }));
	}

	async function ConfirmMarker() {
		await controller.moveToMarkerAsync();
	}

	function SelectUnit(unitId: number, event: MouseEvent) {
		event.stopPropagation();
		controller.selectUnit(unitId);
	}

	function CancleMarker() {
		controller.cancelMarker();
	}

	async function OnKeyDown(event: KeyboardEvent) {
		const key = event.key.toLowerCase();
		if (key === 'c') controller.cancelMarker();
		if (key === 'm') await controller.moveToMarkerAsync();
	}
</script>

<svelte:window onkeydown={OnKeyDown} />

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
{#snippet mapSvgSnippet()}
	{#if controller.state.type === 'selected'}
		{@const selectedUnit = controller.state.selectedUnit}
		<g class="transparent-icons">
			<circle
				cx={selectedUnit.position.x}
				cy={selectedUnit.position.y}
				r="10"
				class="select-circle"
			/>
		</g>
	{:else if controller.state.type == 'marked'}
		{@const selectedUnit = controller.state.selectedUnit}
		{@const moveMarker = controller.state.moveMarker}
		<g class="transparent-icons">
			<circle
				cx={selectedUnit.position.x}
				cy={selectedUnit.position.y}
				r="10"
				class="select-circle"
			/>
			<circle cx={moveMarker.x} cy={moveMarker.y} r="5" class="move-circle" />
			<Arrow start={controller.state.selectedUnit.position} end={controller.state.moveMarker} />
		</g>
	{/if}

	{#each controller.unitData.squads as unit, index}
		<g onclick={(event) => SelectUnit(unit.unitId, event)}>
			<RifleSquad bind:rifleSquadData={controller.unitData.squads[index]} />
		</g>
	{/each}
{/snippet}

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div bind:this={clickTarget} onclick={AddMarker}>
	<SvgMap svgSnippet={mapSvgSnippet} terrainData={controller.terrainData} bind:this={map} />
</div>

{#if controller.state.type == 'marked'}
	<div class="action-box">
		<button onclick={ConfirmMarker}>Move (m)</button>
	</div>
{/if}

{#if controller.state.type != 'default'}
	<div class="info-box">
		<button onclick={CancleMarker}>Cancel (c)</button>
		<br />
		<p>
			Unit #{controller.state.selectedUnit.unitId},
			{controller.state.selectedUnit.status}
		</p>
	</div>
{/if}

<style lang="less">
	* {
		font-size: large;
		font-family: Verdana, Geneva, Tahoma, sans-serif;
	}
	.action-box {
		position: absolute;
		top: 0%;
		right: 0%;
		padding: 1em;
	}
	.info-box {
		position: absolute;
		top: 0%;
		left: 0%;
		padding: 1em;
	}
	.move-circle {
		fill: red;
	}
	.select-circle {
		fill: black;
	}
	.transparent-icons {
		opacity: 0.5;
	}
	.selected-unit {
		transform: translate(1.1, 1.1);
	}
	.move-line {
		stroke: black;
		stroke-width: 3px;
	}
</style>
