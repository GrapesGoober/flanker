<script lang="ts">
	import { onMount } from 'svelte';
	import { PlayerController } from './player-controller.svelte';
	import ControlPanel from './control-panel.svelte';
	import GameplayMap from './gameplay-map.svelte';

	let controller: PlayerController = $state(new PlayerController());

	onMount(async () => {
		await controller.initializeAsync();
	});
</script>

<GameplayMap bind:controller />
<ControlPanel bind:controller />
