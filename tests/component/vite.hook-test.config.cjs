// Temporary vite config — builds ONLY the hook-transition test entry.
// Not part of the shipped bundle.
const path = require('node:path');

module.exports = {
  root: path.resolve(__dirname, '../../component'),
  resolve: {
    alias: [
      { find: /^react(\/.*)?$/, replacement: path.resolve(__dirname, '../../component/node_modules/react$1') },
      { find: /^react-dom(\/.*)?$/, replacement: path.resolve(__dirname, '../../component/node_modules/react-dom$1') },
    ],
  },
  build: {
    lib: {
      entry: path.resolve(__dirname, 'hook_transition_entry.tsx'),
      name: 'hookTransition',
      formats: ['iife'],
      fileName: () => 'hook-transition-test.js',
    },
    outDir: path.resolve(__dirname, 'dist-test'),
    emptyOutDir: true,
    minify: false,
  },
  define: { 'process.env.NODE_ENV': JSON.stringify('test') },
};
