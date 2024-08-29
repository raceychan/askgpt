import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
    client: '@hey-api/client-axios',
    input: 'http://localhost:5000/v1/openapi.json',
    output: { format: 'biome', lint: 'biome', path: 'src/lib/api' },
    services: {
        asClass: true,
    },
});