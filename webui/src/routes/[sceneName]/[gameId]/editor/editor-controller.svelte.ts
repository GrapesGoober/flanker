import { GetTerrainData, UpdateTerrainData, type TerrainModel, type Vec2 } from '$lib/api';

type EditorControllerState =
	| { type: 'default' }
	| { type: 'selected'; terrain: TerrainModel }
	| { type: 'draw'; drawPolygon: Vec2[] };

/**
 * Controller for managing terrain editing and polygon drawing in the editor.
 * Handles terrain data, selection, drawing mode, and state transitions.
 */
export class EditorController {
	terrainData: TerrainModel[] = $state([]);
	state: EditorControllerState = $state({ type: 'default' });

	/** Refreshes terrain data from the API. */
	refreshTerrain() {
		GetTerrainData().then((data) => {
			this.terrainData = data;
		});
	}
	/** Adds a vertex to the current draw polygon if in draw mode. */
	addVertex(worldPos: Vec2) {
		if (this.state.type != 'draw') return;
		this.state.drawPolygon.push(worldPos);
	}
	/** Selects a terrain object and updates its data if already selected. */
	selectTerrain(terrain: TerrainModel) {
		if (this.state.type != 'default' && this.state.type != 'selected') return;
		if (this.state.type == 'selected') UpdateTerrainData(this.state.terrain);
		this.state = {
			type: 'selected',
			terrain: terrain
		};
	}
	/** Asynchronously updates the selected terrain data via the API. */
	async updateTerrainAsync() {
		if (this.state.type != 'selected') return;
		await UpdateTerrainData(this.state.terrain);
	}
	/** Resets the editor state to default. */
	reset() {
		this.state = { type: 'default' };
	}
	/** Switches the editor to draw mode and initializes a new polygon. */
	drawMode() {
		this.state = { type: 'draw', drawPolygon: [] };
	}
}
