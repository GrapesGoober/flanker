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
	<div class="info-box white-translucent-box">
		<button onclick={CancleMarker}>Cancel (c)</button>
		<p>
			Unit #{controller.state.selectedUnit.unitId},
			{controller.state.selectedUnit.isFriendly ? 'Friendly' : 'Hostile'},
			{controller.state.selectedUnit.status}
			{controller.state.selectedUnit.noFire ? ', No Fire' : ''}
		</p>
	</div>

	<div class="action-box white-translucent-box">
		<button onclick={ConfirmMarker} class={controller.isMoveValid() ? '' : 'invalid-button'}>
			Move (m)
		</button>
		<button onclick={ConfirmMarker} class={controller.isFireValid() ? '' : 'invalid-button'}>
			Fire (f)
		</button>
	</div>
{/if}

<style lang="less">
	@spacing: 1em;

	* {
		font-family: Verdana, Geneva, Tahoma, sans-serif;
		display: block;
		margin: @spacing;
	}

	.white-translucent-box {
		background-color: rgba(255, 255, 255, 0.3);
		border: 1px solid rgba(0, 0, 0, 0.3);
	}

	.action-box {
		position: absolute;
		top: 0px;
		right: 0px;
	}
	.info-box {
		position: absolute;
		top: 0px;
		left: 0px;
	}

	.invalid-button {
		opacity: 0.5;
		text-decoration: line-through;
	}
</style>
