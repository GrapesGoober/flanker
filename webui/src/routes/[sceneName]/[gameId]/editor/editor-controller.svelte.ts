import {
	GetTerrainData,
	UpdateTerrainData,
	UpdateWaypointsData,
	type AiWaypointsModel,
	type TerrainModel,
	type Vec2
} from '$lib/api';

type EditorControllerState =
	| { type: 'default' }
	| { type: 'selected'; terrain: TerrainModel }
	| { type: 'draw'; drawPolygon: Vec2[] }
	| { type: 'draw-waypoints'; waypoints: AiWaypointsModel };

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
	/** Switches the editor to draw-waypoints mode and sets a new empty waypoints list. */
	waypointsMode(faction: 'BLUE' | 'RED') {
		this.state = { type: 'draw-waypoints', waypoints: { faction, points: [] } };
	}
	/** Adds a new waypoint */
	addWaypoint(point: Vec2) {
		if (this.state.type != 'draw-waypoints') return;
		this.state.waypoints.points.push(point);
	}
	/** Async updates the waypoints to server */
	async updateWaypoint() {
		if (this.state.type != 'draw-waypoints') return;
		await UpdateWaypointsData(this.state.waypoints);
	}
	/** Finishes the draw and saves the polygon as a new forest terrain. */
	async finishDraw() {
		if (this.state.type != 'draw' || this.state.drawPolygon.length < 3) return;
		const polygon = this.state.drawPolygon;
		const position = polygon[0];
		const vertices = polygon.map((v) => ({ x: v.x - position.x, y: v.y - position.y }));
		const maxId =
			this.terrainData.length > 0 ? Math.max(...this.terrainData.map((t) => t.terrainId)) : 0;
		const terrain: TerrainModel = {
			terrainId: maxId + 1,
			position: position,
			degrees: 0,
			vertices: vertices,
			terrainType: 'FOREST'
		};
		await UpdateTerrainData(terrain);
		this.refreshTerrain();
		this.reset();
	}
}
