<script lang="ts">
	import { onMount } from 'svelte';
	import { PlayerController } from './player-controller.svelte';

	let { controller = $bindable<PlayerController>() } = $props();

	onMount(async () => {
		await controller.initializeAsync();
	});

	async function ConfirmMarker() {
		await controller.confirmMarkerAsync();
	}

	function CancleMarker() {
		controller.cancelMarker();
	}

	async function OnKeyDown(event: KeyboardEvent) {
		const key = event.key.toLowerCase();
		if (key === 'c') controller.cancelMarker();
		else if (key === 'm' && controller.isMoveValid()) await controller.confirmMarkerAsync();
		else if (key === 'f' && controller.isFireValid()) await controller.confirmMarkerAsync();
	}
</script>

<svelte:window onkeydown={OnKeyDown} />

{#if controller.state.type != 'default'}
	<div class="info-box">
		<button onclick={CancleMarker}>Cancel (c)</button>
		<br />
		<p>
			Unit #{controller.state.selectedUnit.unitId},
			{controller.state.selectedUnit.isFriendly ? 'Friendly' : 'Hostile'},
			{controller.state.selectedUnit.status}
			{controller.state.selectedUnit.noFire ? ', No Fire' : ''}
		</p>
	</div>

	<div class="action-box">
		<button onclick={ConfirmMarker} class={controller.isMoveValid() ? '' : 'invalid-option'}
			>Move (m)</button
		>
		<button onclick={ConfirmMarker} class={controller.isFireValid() ? '' : 'invalid-option'}
			>Fire (f)</button
		>
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
	.invalid-option {
		opacity: 0.5;
		text-decoration: line-through;
	}
</style>
