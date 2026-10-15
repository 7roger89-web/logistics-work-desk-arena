// Locally bundled licensed fonts: no external font service/network required.
// Streamlit v2 styles live in a ShadowRoot; register faces on document.fonts
// (CSS @font-face inside a shadow stylesheet is not consistently supported).
import face0 from './assets/fonts/be-vietnam-pro-latin-400-normal.woff2?url';
import face1 from './assets/fonts/be-vietnam-pro-vietnamese-400-normal.woff2?url';
import face2 from './assets/fonts/be-vietnam-pro-latin-500-normal.woff2?url';
import face3 from './assets/fonts/be-vietnam-pro-vietnamese-500-normal.woff2?url';
import face4 from './assets/fonts/be-vietnam-pro-latin-600-normal.woff2?url';
import face5 from './assets/fonts/be-vietnam-pro-vietnamese-600-normal.woff2?url';
import face6 from './assets/fonts/be-vietnam-pro-latin-700-normal.woff2?url';
import face7 from './assets/fonts/be-vietnam-pro-vietnamese-700-normal.woff2?url';
import face8 from './assets/fonts/be-vietnam-pro-latin-800-normal.woff2?url';
import face9 from './assets/fonts/be-vietnam-pro-vietnamese-800-normal.woff2?url';
import face10 from './assets/fonts/ibm-plex-mono-latin-400-normal.woff2?url';
import face11 from './assets/fonts/ibm-plex-mono-vietnamese-400-normal.woff2?url';
import face12 from './assets/fonts/ibm-plex-mono-latin-500-normal.woff2?url';
import face13 from './assets/fonts/ibm-plex-mono-vietnamese-500-normal.woff2?url';
import face14 from './assets/fonts/ibm-plex-mono-latin-600-normal.woff2?url';
import face15 from './assets/fonts/ibm-plex-mono-vietnamese-600-normal.woff2?url';
import face16 from './assets/fonts/ibm-plex-mono-latin-700-normal.woff2?url';
import face17 from './assets/fonts/ibm-plex-mono-vietnamese-700-normal.woff2?url';

const faces = [
  ['Be Vietnam Pro', face0, '400', 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD'],
  ['Be Vietnam Pro', face1, '400', 'U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB'],
  ['Be Vietnam Pro', face2, '500', 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD'],
  ['Be Vietnam Pro', face3, '500', 'U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB'],
  ['Be Vietnam Pro', face4, '600', 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD'],
  ['Be Vietnam Pro', face5, '600', 'U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB'],
  ['Be Vietnam Pro', face6, '700', 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD'],
  ['Be Vietnam Pro', face7, '700', 'U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB'],
  ['Be Vietnam Pro', face8, '800', 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD'],
  ['Be Vietnam Pro', face9, '800', 'U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB'],
  ['IBM Plex Mono', face10, '400', 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD'],
  ['IBM Plex Mono', face11, '400', 'U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB'],
  ['IBM Plex Mono', face12, '500', 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD'],
  ['IBM Plex Mono', face13, '500', 'U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB'],
  ['IBM Plex Mono', face14, '600', 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD'],
  ['IBM Plex Mono', face15, '600', 'U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB'],
  ['IBM Plex Mono', face16, '700', 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD'],
  ['IBM Plex Mono', face17, '700', 'U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB'],
];
let registered = false;
export function ensureFonts() {
  if (registered || typeof FontFace === 'undefined') return;
  registered = true;
  for (const [family, url, weight, unicodeRange] of faces) {
    const face = new FontFace(family, `url("${url}")`, { weight, unicodeRange, display: 'swap' });
    document.fonts.add(face);
    void face.load().catch(() => { /* browser keeps its normal fallback on failure */ });
  }
}
