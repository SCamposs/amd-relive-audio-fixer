import {defineConfig} from 'vite';
export default defineConfig({base:'./',build:{outDir:'dist',rollupOptions:{onwarn(warning, handler){if(warning.code==='MODULE_LEVEL_DIRECTIVE')return;handler(warning);}}}});
