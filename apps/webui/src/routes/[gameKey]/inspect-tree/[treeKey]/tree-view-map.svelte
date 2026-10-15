<script lang="ts">
	import type { GameViewState, MapViewState } from '$lib/api';
	import { RifleSquad, SvgMap, TerrainLayer } from '$lib/components';

	type Props = {
		mapData: MapViewState;
		viewState: GameViewState;
	};

	let { mapData, viewState }: Props = $props();
</script>

{#snippet mapContent()}
	<TerrainLayer {mapData} />
	<svg overflow="visible">
		{#each viewState.squads as squad}
			<RifleSquad rifleSquadData={squad} />
		{/each}
	</svg>
{/snippet}

<SvgMap svgSnippet={mapContent} />
