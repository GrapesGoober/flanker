import {
	AddTerrainData,
	DeleteTerrainData,
	GetTerrainData,
	UpdateTerrainData,
	UpdateWaypointsData,
	type AiWaypointsModel,
	type TerrainModel,
	type Vec2
} from '$lib/api';
import { transform } from '$lib/map-utils';

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

	/** Adds a vertex to the current draw polygon if in draw mode. */
	addVertex(worldPos: Vec2) {
		if (this.state.type != 'draw') return;
		this.state.drawPolygon.push(worldPos);
	}
	/** Finishes the draw and saves the polygon as a new forest terrain. */
	async finishDraw() {
		if (this.state.type != 'draw' || this.state.drawPolygon.length < 3) return;
		const polygon = this.state.drawPolygon;
		const position = polygon[0]; // Assume first polygon as position
		if (position === undefined) return;
		const vertices = transform(polygon, { x: -position.x, y: -position.y }, 0);
		const terrain: TerrainModel = {
			// The ID is ignored as it will create a new one
			// The pain of not using UUID is haunting me
			terrainId: 0,
			position: position,
			degrees: 0,
			vertices: vertices,
			terrainType: 'FOREST' // TODO: add a select box to choose terrain
		};
		await AddTerrainData(terrain);
		this.refreshTerrain();
		this.reset();
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

	/** Deletes the selected terrain */
	async deleteTerrain() {
		if (this.state.type != 'selected') return;
		await DeleteTerrainData(this.state.terrain.terrainId);
	}
	/** Asynchronously updates the selected terrain data via the API. */
	async updateTerrainAsync() {
		if (this.state.type != 'selected') return;
		await UpdateTerrainData(this.state.terrain);
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
}
