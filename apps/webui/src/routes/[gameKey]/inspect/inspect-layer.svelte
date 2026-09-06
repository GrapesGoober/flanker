<script lang="ts">
	import type { GameStateInspection } from '$lib/api';
	import { RifleSquad } from '$lib/components';
	import { GetClosedPath } from '$lib/map-utils';

	type Props = {
		inspectionData: GameStateInspection;
	};

	let props: Props = $props();
</script>

<!-- Draw the combat units -->
<svg overflow="visible">
	{#each props.inspectionData.viewState.squads as unit}
		<RifleSquad rifleSquadData={unit} />
	{/each}

	{#each props.inspectionData.losPolygons as losPolygon}
		{#if losPolygon.faction == 'BLUE'}
			<path d={GetClosedPath(losPolygon.losPolygon)} class="blue-los" />
		{:else if losPolygon.faction == 'RED'}
			<path d={GetClosedPath(losPolygon.losPolygon)} class="red-los" />
		{/if}
	{/each}
</svg>

<style lang="less">
	@los-stroke-width: 1;
	* {
		font-size: large;
		font-family: Verdana, Geneva, Tahoma, sans-serif;
	}
	.blue-los {
		fill: #5eb0ef1b;
		stroke: #5eb0ef75;
		stroke-width: los-stroke-width;
		stroke-linecap: square;
	}
	.red-los {
		fill: #efab5e23;
		stroke: #efab5e77;
		stroke-width: los-stroke-width;
		stroke-linecap: square;
	}
</style>
