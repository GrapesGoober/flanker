<script lang="ts">
	import { onMount } from 'svelte';
	import RifleSquad from '$lib/rifle-squad.svelte';
	import SvgMap from '$lib/map/svg-map.svelte';
	import Arrow from '$lib/svg-icons/arrow.svelte';
	import { PlayerState } from './player-state.svelte';

	let map: SvgMap | null = $state(null);
	let clickTarget: HTMLElement | null = $state(null);
	let playerState: PlayerState = $state(new PlayerState());

	onMount(async () => {
		await playerState.initializeAsync();
	});

	function AddMarker(event: MouseEvent) {
		if (map == null) return;
		const node = clickTarget as HTMLElement;
		const rect = node.getBoundingClientRect();
		const x = event.clientX - rect.x;
		const y = event.clientY - rect.y;
		playerState.addMoveMarker(map.ToWorldCoords({ x, y }));
	}

	async function ConfirmMarker() {
		await playerState.moveToMarkerAsync();
	}

	function SelectUnit(unitId: number, event: MouseEvent) {
		event.stopPropagation();
		playerState.selectUnit(unitId);
	}

	function CancleMarker() {
		playerState.cancelMarker();
	}

	async function OnKeyDown(event: KeyboardEvent) {
		const key = event.key.toLowerCase();
		if (key === 'c') playerState.cancelMarker();
		if (key === 'm') await playerState.moveToMarkerAsync();
	}
</script>

<svelte:window onkeydown={OnKeyDown} />

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
{#snippet mapSvgSnippet()}
	{#if playerState.moveMarker && playerState.selectedUnit}
		<circle cx={playerState.moveMarker.x} cy={playerState.moveMarker.y} r="5" class="move-circle" />
		<Arrow start={playerState.selectedUnit.position} end={playerState.moveMarker} />
	{/if}

	{#each playerState.unitData.squads as unit, index}
		{#if playerState.unitData.squads[index]}
			<g onclick={(event) => SelectUnit(unit.unitId, event)}>
				<RifleSquad bind:rifleSquadData={playerState.unitData.squads[index]} />
			</g>
		{/if}
	{/each}
{/snippet}

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div bind:this={clickTarget} onclick={AddMarker}>
	<SvgMap svgSnippet={mapSvgSnippet} terrainData={playerState.terrainData} bind:this={map} />
</div>

{#if playerState.moveMarker}
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
