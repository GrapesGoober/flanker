<script lang="ts">
	import type { GameStateInspection } from '$lib/api';
	import { RifleSquad } from '$lib/components';
	import { GetClosedPath } from '$lib/map-utils';

	type Props = {
		inspectionData: GameStateInspection;
		drawFov: boolean;
		drawMoveCandidates: boolean;
	};
	let {
		inspectionData,
		drawFov = $bindable(),
		drawMoveCandidates = $bindable()
	}: Props = $props();
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

	{#if drawMoveCandidates}
		{#each inspectionData.moveCandidates as moveCandidate}
			<circle
				cx={moveCandidate.x}
				cy={moveCandidate.y}
				class="move-candidate"
			/>
		{/each}
	{/if}
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
	.move-candidate {
		fill: rgb(255, 132, 0);
		r: 3;
	}
</style>
