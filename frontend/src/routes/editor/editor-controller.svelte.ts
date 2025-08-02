import { getTerrainData, type TerrainFeatureData, type Vec2 } from '$lib';

type EditorControllerState =
	| { type: 'default' }
	| { type: 'select'; selectedTerrain: TerrainFeatureData | null }
	| { type: 'draw'; drawPolygon: Vec2[] };

export class EditorController {
	terrainData: TerrainFeatureData[] = $state([]);
	state: EditorControllerState = $state({ type: 'default' });

	refreshTerrain() {
		getTerrainData().then((data) => {
			this.terrainData = data;
		});
	}
	addVertex(worldPos: Vec2) {
		if (this.state.type != 'draw') return;
		this.state.drawPolygon.push(worldPos);
	}
	selectTerrain(terrain: TerrainFeatureData) {
		if (this.state.type != 'select') return;
		this.state.selectedTerrain = terrain;
	}
	reset() {
		this.state = { type: 'default' };
	}
	drawMode() {
		this.state = { type: 'draw', drawPolygon: [] };
	}
	selectMode() {
		this.state = { type: 'select', selectedTerrain: null };
	}
}
