<script lang="ts">
	import { onMount } from 'svelte';
	import RifleSquad from '$lib/rifle-squad.svelte';
	import SvgMap from '$lib/map/svg-map.svelte';
	import Arrow from '$lib/svg-icons/arrow.svelte';
	import {
		addMarker,
		cancleMarker,
		initializePlayerState,
		moveToMarkerAsync,
		newPlayerState,
		selectUnit,
		type PlayerStateContext
	} from './player-state';

	let map: SvgMap | null = $state(null);
	let clickTarget: HTMLElement | null = $state(null);
	let playerState: PlayerStateContext = $state(newPlayerState());

	onMount(async () => {
		await initializePlayerState(playerState);
	});

	function AddMarker(event: MouseEvent) {
		if (map == null) return;

		let node = clickTarget as HTMLElement;
		let rect = node.getBoundingClientRect();
		let x = event.clientX - rect.x; //x position within the element.
		let y = event.clientY - rect.y; //y position within the element.
		addMarker(playerState, map.ToWorldCoords({ x, y }));
	}

	async function ConfirmMarker() {
		await moveToMarkerAsync(playerState);
	}

	function SelectUnit(unitId: number, event: MouseEvent) {
		event.stopPropagation(); // No carryover to map's onclick
		selectUnit(playerState, unitId);
	}

	function CancleMarker() {
		cancleMarker(playerState);
	}

	async function OnKeyDown(event: KeyboardEvent) {
		if (event.key.toLowerCase() === 'c') {
			cancleMarker(playerState);
		}
		if (event.key.toLowerCase() === 'm') {
			moveToMarkerAsync(playerState);
		}
	}
</script>

<svelte:window onkeydown={OnKeyDown} />

<!-- I'm prototying behaviours at the moment, so proper structure comes later -->
<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
{#snippet mapSvgSnippet()}
	{#if playerState.marker && playerState.selectedUnit}
		<circle cx={playerState.marker.x} cy={playerState.marker.y} r="5" class="move-circle" />
		<Arrow start={playerState.selectedUnit.position} end={playerState.marker} />
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

{#if playerState.marker}
	<div class="action-box">
		<button onclick={CancleMarker} class="action-button">Cancel (c)</button>
		<br />
		<br />
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
