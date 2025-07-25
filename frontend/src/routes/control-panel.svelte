<script lang="ts">
	import { PlayerController } from './player-controller.svelte';

	let { controller = $bindable<PlayerController>() } = $props();

	async function confirmMarker() {
		await controller.confirmMarkerAsync();
	}

	function closeSelection() {
		controller.closeSelection();
	}

	async function onKeyDown(event: KeyboardEvent) {
		const key = event.key.toLowerCase();
		if (key === 'c') controller.closeSelection();
		else if (key === 'm' && controller.isMoveValid()) await controller.confirmMarkerAsync();
		else if (key === 'f' && controller.isFireValid()) await controller.confirmMarkerAsync();
	}
</script>

<svelte:window onkeydown={onKeyDown} />

{#if controller.state.type != 'default'}
	<div class="info-box">
		<div class="info-header-box">
			<span class="info-header-text">1st Platoon</span>
			<button class="info-header-close-button" onclick={closeSelection}>Close (c)</button>
		</div>
		<span class="info-detail">
			Squad {controller.state.selectedUnit.unitId},
			{controller.state.selectedUnit.isFriendly ? 'Friendly' : 'Hostile'},
			{controller.state.selectedUnit.status}
			{controller.state.selectedUnit.noFire ? ', No Fire' : ''}
		</span>
	</div>

	<div class="action-box">
		<button
			onclick={confirmMarker}
			class={controller.isMoveValid() ? 'valid-button' : 'invalid-button'}
		>
			Move (m)
		</button>
		<button
			onclick={confirmMarker}
			class={controller.isFireValid() ? 'valid-button' : 'invalid-button'}
		>
			Fire (f)
		</button>
	</div>
{/if}

<style lang="less">
	@spacing: 15px;
	@opacity: 0.5;
	@background-color: rgba(255, 255, 255, @opacity);
	@border-color: rgba(0, 0, 0, @opacity);
	@border: 1px solid @border-color;

	// Globals
	* {
		font-family: Verdana, Geneva, Tahoma, sans-serif;
	}

	// Info Section
	.info-box {
		position: absolute;
		top: 0px;
		left: 0px;
		margin: @spacing;
		background-color: @background-color;
		border: @border;
	}
	.info-header-box {
		display: block;
		margin: @spacing;
	}
	.info-header-text {
		display: inline;
		font-size: large;
	}
	.info-header-close-button {
		display: inline;
		margin: 0 @spacing; /* Horizontal Spacing */
		float: right; /* Align to right side of box*/
	}

	.info-detail {
		display: block;
		margin: @spacing;
	}

	// Action Section
	.action-box {
		position: absolute;
		top: 0px;
		right: 0px;
		margin: @spacing;
		background-color: @background-color;
		border: @border;
	}
	.valid-button {
		display: block;
		margin: @spacing;
	}
	.invalid-button {
		display: block;
		margin: @spacing;
		opacity: 0.5;
		text-decoration: line-through;
	}
</style>
