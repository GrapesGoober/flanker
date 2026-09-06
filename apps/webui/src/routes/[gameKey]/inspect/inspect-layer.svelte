<script lang="ts">
	import type { GameStateInspection } from '$lib/api';
	import { RifleSquad } from '$lib/components';
	import { GetClosedPath } from '$lib/map-utils';

	type Props = {
		inspectionData: GameStateInspection;
		drawFov: boolean;
		drawMoveCandidates: boolean;
		drawUnitTexts: boolean;
	};
	let {
		inspectionData,
		drawFov = $bindable(),
		drawMoveCandidates = $bindable(),
		drawUnitTexts = $bindable()
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

	{#if drawUnitTexts}
		<!-- Draw unit data last to render on top -->
		{#each inspectionData.viewState.squads as unit}
			<foreignObject
				x={unit.position.x + 10}
				y={unit.position.y - 10}
				width="160"
				height="160"
				class="combat-unit-text"
			>
				{unit.unitId.slice(0, 8)}
				<br />
				({unit.position.x}, {unit.position.y}, {unit.degree}&deg)
				<br />
				{unit.status}
			</foreignObject>
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
	.combat-unit-text {
		font-size: 0.3em;
	}
</style>
