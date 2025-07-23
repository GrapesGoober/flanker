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
	{#if controller.state.type == 'marked'}
		<circle
			cx={controller.state.moveMarker.x}
			cy={controller.state.moveMarker.y}
			r="5"
			class="move-circle"
		/>
		<Arrow start={controller.state.selectedUnit.position} end={controller.state.moveMarker} />
	{/if}

	{#each controller.unitData.squads as unit, index}
		{#if controller.unitData.squads[index]}
			<g onclick={(event) => SelectUnit(unit.unitId, event)}>
				<RifleSquad bind:rifleSquadData={controller.unitData.squads[index]} />
			</g>
		{/if}
	{/each}
{/snippet}

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div bind:this={clickTarget} onclick={AddMarker}>
	<SvgMap svgSnippet={mapSvgSnippet} terrainData={controller.terrainData} bind:this={map} />
</div>

{#if controller.state.type == 'marked'}
	<div class="action-box">
		<button onclick={CancleMarker} class="action-button">Cancel (c)</button>
		<br /><br />
		<button onclick={ConfirmMarker} class="action-button">Move (m)</button>
	</div>
{/if}

<style lang="less">
	.action-box {
		position: absolute;
		top: 0%;
		right: 0%;
		padding: 1em;
	}
	.action-button {
		font-size: large;
	}
	.move-circle {
		fill: red;
		fill-opacity: 0.5;
	}
</style>
