import { chromium } from "playwright";

const volumes = [250, 1000, 5000];
const rounds = 5;
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.setContent("<!doctype html><html><body><div id='root'></div><canvas id='canvas' width='1200' height='360'></canvas></body></html>");
  const report = await page.evaluate(({ volumes, rounds }) => {
    function trips(n) {
      return Array.from({ length: n }, (_, i) => ({
        x1: i % 1180,
        y1: (i * 17) % 330,
        x2: (i * 13 + 60) % 1180,
        y2: (i * 19 + 120) % 330,
      }));
    }
    function median(values) {
      const sorted = [...values].sort((a, b) => a - b);
      return sorted[Math.floor(sorted.length / 2)];
    }
    const root = document.getElementById("root");
    const canvas = document.getElementById("canvas");
    const ctx = canvas.getContext("2d");
    if (!root || !ctx) throw new Error("browser rendering surfaces unavailable");
    return volumes.map((volume) => {
      const data = trips(volume);
      const svgSamples = [];
      const canvasSamples = [];
      for (let r = 0; r < rounds; r += 1) {
        const svgStart = performance.now();
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("width", "1200");
        svg.setAttribute("height", "360");
        const fragment = document.createDocumentFragment();
        for (const trip of data) {
          const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
          line.setAttribute("x1", String(trip.x1)); line.setAttribute("y1", String(trip.y1));
          line.setAttribute("x2", String(trip.x2)); line.setAttribute("y2", String(trip.y2));
          fragment.appendChild(line);
        }
        svg.appendChild(fragment); root.replaceChildren(svg);
        svg.getBoundingClientRect();
        svgSamples.push(performance.now() - svgStart);

        const canvasStart = performance.now();
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.beginPath();
        for (const trip of data) { ctx.moveTo(trip.x1, trip.y1); ctx.lineTo(trip.x2, trip.y2); }
        ctx.stroke();
        ctx.getImageData(0, 0, 1, 1);
        canvasSamples.push(performance.now() - canvasStart);
      }
      return { volume, svgDomMs: median(svgSamples), canvasRasterMs: median(canvasSamples) };
    });
  }, { volumes, rounds });

  const realistic = report.find((row) => row.volume === 1000);
  if (!realistic) throw new Error("missing 1000-trip browser density sample");
  // This is a CI regression guard, not a universal UX/FPS threshold. Chromium
  // must materialize 1000 SVG trajectories in a bounded interval; Canvas is
  // measured alongside it to retain evidence for a future renderer decision.
  if (realistic.svgDomMs > 500) {
    throw new Error(`SVG browser density gate failed: 1000 trips took ${realistic.svgDomMs.toFixed(1)} ms`);
  }
  console.log(JSON.stringify({ status: "PASS", benchmark: "march-density-browser-v1", rounds, report }, null, 2));
} finally {
  await browser.close();
}
