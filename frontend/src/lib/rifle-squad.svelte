<script lang="ts">
	import type { RifleSquadData } from '$lib';
	let { rifleSquadData = $bindable() }: { rifleSquadData: RifleSquadData } = $props();
</script>

<g transform="translate({rifleSquadData.position.x},{rifleSquadData.position.y})">
	{#if rifleSquadData.isFriendly}
		<g class={rifleSquadData.isSelected ? 'unit-icon-selected' : 'unit-icon'}>
			<rect x="-8" y="-8" width="16" height="16" class="box" />
			<line x1="-8" y1="-8" x2="8" y2="8" class="cross" />
			<line x1="8" y1="-8" x2="-8" y2="8" class="cross" />
		</g>
	{:else}
		<polygon points="0,-10 10,0 0,10 -10,0" class="diamond" />
		<line x1="-5" y1="-5" x2="5" y2="5" class="cross" />
		<line x1="5" y1="-5" x2="-5" y2="5" class="cross" />
	{/if}
</g>

<style>
	.unit-icon {
		transform: scale(1, 0.7);
	}
	.unit-icon-selected {
		transform: scale(1.1, 0.8);
	}
	.box {
		fill: white;
		stroke: black;
		stroke-width: 1.5;
	}
	.diamond {
		fill: white;
		stroke: black;
		stroke-width: 1.5;
	}
	.cross {
		stroke: black;
		stroke-width: 1.5;
	}
</style>
