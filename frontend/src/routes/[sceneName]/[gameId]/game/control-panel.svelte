<script lang="ts">
	/*
	ControlPanel displays selected unit info and available actions (move, fire, assault).
	Handles keyboard shortcuts and loading state for player actions.
	*/
	import { LoadingSpinner } from '$lib/components';
	import { PlayerController } from './player-controller.svelte';

	type Props = {
		controller: PlayerController;
	};

	let { controller = $bindable() }: Props = $props();

	/* Closes the current unit selection. */
	function closeSelection() {
		controller.closeSelection();
	}

	/* Handles keyboard shortcuts for unit actions. */
	async function onKeyDown(event: KeyboardEvent) {
		const key = event.key.toLowerCase();
		if (key === 'c') controller.closeSelection();
		else if (key === 'm') await controller.moveActionAsync();
		else if (key === 'f') await controller.fireActionAsync();
		else if (key === 'a') await controller.assaultActionAsync();
	}
</script>

<!-- Listen for keyboard shortcuts to trigger actions -->
<svelte:window onkeydown={onKeyDown} />

{#if controller.state.type != 'default'}
	<!-- Info box: displays selected unit details -->
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

	<!-- Action box: buttons for move, fire, and assault actions -->
	<div class="action-box {controller.isFetching ? 'loading' : ''}">
		<button
			class="action-button"
			onclick={() => {
				controller.moveActionAsync();
			}}
			disabled={!controller.isMoveActionValid()}
		>
			Move (m)
		</button>
		<button
			class="action-button"
			onclick={() => {
				controller.fireActionAsync();
			}}
			disabled={!controller.isFireActionValid()}
		>
			Fire (f)
		</button>
		<button
			class="action-button"
			onclick={() => {
				controller.assaultActionAsync();
			}}
			disabled={!controller.isAssaultActionValid()}
		>
			Assault (a)
		</button>
		{#if controller.isFetching}
			<!-- Loading spinner shown while actions are processing -->
			<div class="loading-spinner">
				<LoadingSpinner />
			</div>
		{/if}
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
		font-family: monospace;
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
	.loading {
		opacity: 0.5;
		transition: opacity 0.3s ease;
	}
	.action-button {
		display: block;
		margin: @spacing;
	}
	.loading-spinner {
		position: absolute;
		opacity: 0.5;
		transition: opacity 0.3s ease;
		transform: translate(100%, -150%);
	}
</style>
