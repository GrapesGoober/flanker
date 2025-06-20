<script lang="ts">
	import type { Vec2 } from '$lib';
	let { position, isSelected }: { position: Vec2; isSelected: boolean } = $props();
</script>

<g transform="translate({position.x},{position.y})">
	<g width="15" height="15" class={isSelected ? 'unit-icon-selected' : 'unit-icon'}>
		<rect x="0" y="0" width="15" height="15" class="box" />
		<line x1="0" y1="0" x2="15" y2="15" class="cross" />
		<line x1="15" y1="0" x2="0" y2="15" class="cross" />
	</g>
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
	.cross {
		stroke: black;
		stroke-width: 1.5;
	}
</style>
