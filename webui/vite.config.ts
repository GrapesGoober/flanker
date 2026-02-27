import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
	const env = loadEnv(mode, process.cwd(), '');
	const webapiUrl = env.VITE_WEBAPI_URL ?? 'http://localhost:8000';
	const webuiPort = env.VITE_WEBUI_PORT ?? '5173';

	return {
		plugins: [sveltekit()],
		server: {
			port: Number(webuiPort),
			proxy: {
				'/api': {
					target: webapiUrl
				}
			}
		}
	};
});
