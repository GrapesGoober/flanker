<script lang="ts">
	import { onMount, type Snippet } from 'svelte';
	import * as d3 from 'd3';
	import type { Vec2 } from '$lib';

	type Props = {
		onclick: (event: MouseEvent, worldPos: Vec2) => void;
		body: Snippet;
	};
	let props: Props = $props();
	let svgLayer: SVGSVGElement | null = null;
	let zoomLayer: SVGGElement | null = null;
	let transform: d3.ZoomTransform = d3.zoomIdentity;

	onMount(() => {
		const svg = d3.select(svgLayer);
		const g = d3.select(zoomLayer);
		const zoom = d3
			.zoom<SVGSVGElement, unknown>()
			.scaleExtent([0.5, 10])
			.on('zoom', (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
				transform = event.transform;
				g.attr('transform', transform.toString());
			});

		svg.call(zoom as any);
	});

	function onclick(event: MouseEvent) {
		// Convert click event to world position vector
		const point = d3.pointer(event, svgLayer); // Get click coords in SVG space
		const worldPos = transform.invert(point); // Adjust for zoom/pan to world space
		const pos: Vec2 = { x: worldPos[0], y: worldPos[1] };
		props.onclick(event, pos);
	}
</script>

<!-- I'm prototying behaviours at the moment, so proper structure comes later -->
<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<svg bind:this={svgLayer} width="100%" height="90vh" style="border: 1px solid #ccc" {onclick}>
	<g bind:this={zoomLayer}>
		{@render props.body()}
	</g>
</svg>

<style>
	svg {
		touch-action: none; /* required for pointer-based zooming */
		background-color: #ecffc7;
	}
</style>
