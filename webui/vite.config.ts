import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
	const env = loadEnv(mode, process.cwd(), '');
	const apiUrl = env.VITE_WEBAPI_URL ?? 'http://localhost:8000';

	return {
		plugins: [sveltekit()],
		server: {
			proxy: {
				'/api': {
					target: apiUrl
				}
			}
		}
	};
});
