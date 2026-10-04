import { performance } from "node:perf_hooks";

const volumes = [250, 1000, 5000];
const rounds = 8;

function trips(n) {
  return Array.from({ length: n }, (_, i) => ({
    x1: i % 1180,
    y1: (i * 17) % 330,
    x2: (i * 13 + 60) % 1180,
    y2: (i * 19 + 120) % 330,
  }));
}

function svgSerialize(data) {
  return data.map((t) => `<line x1="${t.x1}" y1="${t.y1}" x2="${t.x2}" y2="${t.y2}"/>`).join("");
}

function canvasCommandSerialize(data) {
  // Canvas comparison measures the retained JS command preparation cost, not
  // browser rasterization. It is a technology-density signal, not an FPS claim.
  return data.map((t) => ["M", t.x1, t.y1, "L", t.x2, t.y2]);
}

function measure(fn, data) {
  const samples = [];
  for (let r = 0; r < rounds; r += 1) {
    const start = performance.now();
    const output = fn(data);
    if (output.length !== data.length && typeof output !== "string") throw new Error("invalid benchmark output");
    samples.push(performance.now() - start);
  }
  samples.sort((a, b) => a - b);
  return samples[Math.floor(samples.length / 2)];
}

const report = [];
for (const volume of volumes) {
  const data = trips(volume);
  const svgMs = measure(svgSerialize, data);
  const canvasMs = measure(canvasCommandSerialize, data);
  report.push({ volume, svgMs: Number(svgMs.toFixed(3)), canvasPreparationMs: Number(canvasMs.toFixed(3)) });
}

console.log(JSON.stringify({ benchmark: "march-density-v1", rounds, report }, null, 2));

const realistic = report.find((row) => row.volume === 1000);
if (!realistic || realistic.svgMs > 100) {
  console.error("SVG density gate failed: 1000-trip serialization exceeded 100 ms");
  process.exit(1);
}
