<script lang="ts">
	import type { GameViewState } from '$lib/api';
	import { RifleSquad } from '$lib/components';

	type Props = {
		viewState: GameViewState;
	};

	let props: Props = $props();
</script>

<!-- Draw the combat units -->
<svg overflow="visible">
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	{#each props.viewState.squads as unit, index}
		<RifleSquad bind:rifleSquadData={props.viewState.squads[index]} />
	{/each}
</svg>

<style lang="less">
	* {
		font-size: large;
		font-family: Verdana, Geneva, Tahoma, sans-serif;
	}
</style>
