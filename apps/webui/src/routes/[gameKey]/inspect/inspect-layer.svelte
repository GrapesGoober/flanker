<script lang="ts">
	import type { GameStateInspection } from '$lib/api';
	import { RifleSquad } from '$lib/components';
	import { GetClosedPath } from '$lib/map-utils';

	type Props = {
		inspectionData: GameStateInspection;
		drawFov: boolean;
	};
	let { inspectionData, drawFov = $bindable() }: Props = $props();
</script>

<svg overflow="visible">
	{#each inspectionData.viewState.squads as unit}
		<RifleSquad rifleSquadData={unit} />
	{/each}

	{#each inspectionData.losPolygons as losPolygon}
		{@const polygon = drawFov ? losPolygon.fovPolygon : losPolygon.losPolygon}

		{#if losPolygon.faction === 'BLUE'}
			<path d={GetClosedPath(polygon)} class="blue-los" />
		{:else if losPolygon.faction === 'RED'}
			<path d={GetClosedPath(polygon)} class="red-los" />
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
