<script lang="ts">
	import type { Vec2 } from '$lib';
	let { position }: { position: Vec2 } = $props();
</script>

<g transform="translate({position.x},{position.y})">
	<g width="30" height="30" class="unit-icon" >
		<rect x="5" y="5" width="20" height="20" class="box" />
		<line x1="5" y1="5" x2="25" y2="25" class="cross" />
		<line x1="25" y1="5" x2="5" y2="25" class="cross" />
	</g>
</g>

<style>
	.unit-icon {
		transform: scale(1, 0.7);
	}
	.box {
		fill: white;
		stroke: black;
		stroke-width: 2;
	}
	.cross {
		stroke: black;
		stroke-width: 2;
	}
</style>
