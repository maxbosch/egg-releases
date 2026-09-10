export const EGG_COUNT = 18;
export const EGG_COLORS = ['#ffb929', '#fa775d', '#eee9d8', '#b5a0ed', '#93c8ed', '#c6d771'];
export const clamp = (n: number, a = 0, b = 1) => Math.max(a, Math.min(b, n));
export const smooth = (n: number) => { const t = clamp(n); return t * t * (3 - 2 * t); };
export const seed = (n: number) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
export const terrainHeight = (x: number, z: number) => .14 * Math.sin(x * .62) * Math.cos(z * .57) + .08 * Math.sin(z * 1.1);
export function meadowPosition(index: number): [number, number, number] {
  const col = index % 6, row = Math.floor(index / 6);
  const x = (col - 2.5) * 1.75 + (seed(index + 11) - .5) * .4;
  const z = (row - 1) * 2.5 - .65 + (seed(index + 21) - .5) * .55;
  return [x, terrainHeight(x, z) + .48, z];
}
export function scrollPhases(scrollY: number, height: number, meadowTop: number) {
  return {
    crack: smooth((scrollY / height - .04) / .48),
    burst: smooth((scrollY / height - .42) / .82),
    meadow: smooth((scrollY - meadowTop + height * .95) / (height * .85)),
  };
}
export function collectEgg(current: readonly number[], id: number) {
  return Number.isInteger(id) && id >= 0 && id < EGG_COUNT && !current.includes(id) ? [...current, id] : [...current];
}
