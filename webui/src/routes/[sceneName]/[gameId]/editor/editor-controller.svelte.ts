import {
	AddTerrainData,
	DeleteTerrainData,
	GetTerrainData,
	UpdateTerrainData,
	UpdateWaypointsData,
	type AiWaypointsModel,
	type TerrainModel,
	type TerrainType,
	type Vec2
} from '$lib/api';
import { transform } from '$lib/map-utils';

type EditorControllerState =
	| { type: 'default' }
	| { type: 'selected'; terrain: TerrainModel }
	| { type: 'draw'; drawPolygon: Vec2[]; terrainType: TerrainType }
	| { type: 'draw-waypoints'; waypoints: AiWaypointsModel };

/**
 * Controller for managing terrain editing and polygon drawing in the editor.
 * Handles terrain data, selection, drawing mode, and state transitions.
 */
export class EditorController {
	terrainData: TerrainModel[] = $state([]);
	state: EditorControllerState = $state({ type: 'default' });
	isFetching: boolean = $state(false);
	errorMessage: string | null = $state(null);
	errorLog: string[] = $state([]);

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

	/** Clears currently shown error text. */
	clearError() {
		this.errorMessage = null;
	}
	/** Switches the editor to draw mode and initializes a new polygon. */
	drawMode() {
		this.state = { type: 'draw', drawPolygon: [], terrainType: 'FOREST' };
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
			terrainId: crypto.randomUUID(),
			position: position,
			degrees: 0,
			vertices: vertices,
			terrainType: this.state.terrainType
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

	/** Runs an async request with UI-safe state transitions and error recording. */
	private async executeRequestAsync(context: string, request: () => Promise<void>): Promise<boolean> {
		if (this.isFetching) return false;
		this.isFetching = true;
		this.clearError();
		try {
			await request();
			return true;
		} catch (error) {
			this.reportError(context, error);
			return false;
		} finally {
			this.isFetching = false;
		}
	}

	/** Stores a readable error for the editor and keeps a short history. */
	private reportError(context: string, error: unknown) {
		const details =
			error instanceof Error ? error.message : typeof error === 'string' ? error : 'Unknown error';
		const message = `${context}. ${details}`;
		this.errorMessage = message;
		this.errorLog = [`${new Date().toLocaleTimeString()} ${message}`, ...this.errorLog].slice(0, 6);
	}
}
