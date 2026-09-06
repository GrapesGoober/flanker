<script lang="ts">
	import type { GameStateInspection } from '$lib/api';
	import { RifleSquad } from '$lib/components';

	type Props = {
		inspectionData: GameStateInspection;
	};

	let props: Props = $props();
</script>

<!-- Draw the combat units -->
<svg overflow="visible">
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	{#each props.inspectionData.viewState.squads as unit}
		<RifleSquad rifleSquadData={unit} />
	{/each}
</svg>

<style lang="less">
	* {
		font-size: large;
		font-family: Verdana, Geneva, Tahoma, sans-serif;
	}
</style>
