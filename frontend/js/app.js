import { fetchTargets } from "./api.js";
import { renderTargets, attachRowClickHandler } from "./table.js";
import { initModal, openTargetModal } from "./modal.js";

const status = document.getElementById("status");
const refreshBtn = document.getElementById("refreshBtn");
const fromSystemInput = document.getElementById("fromSystem");
const scoreHeader = document.getElementById("scoreHeader");
const resultsCount = document.getElementById("resultsCount");

let sortDescending = true;
let currentTargets = [];

function formatValue(value) {
  return value != null && value !== "" ? String(value) : "N/A";
}

function getRowCells(target) {
  return [
    formatValue(target.system_name),
    formatValue(target.region_name),
    formatValue(target.constellation_name),
    formatValue(target.distance),
    target.score != null ? Number(target.score).toFixed(1) : "N/A",
    formatValue(target.npc_kills),
    formatValue(target.ship_kills),
    formatValue(target.pod_kills),
    formatValue(target.jumps),
  ];
}

function updateScoreHeader() {
  scoreHeader.textContent = `score ${sortDescending ? "▼" : "▲"}`;
}

function handleTargetSelection(index) {
  const target = currentTargets[index];
  if (target) {
    openTargetModal(target);
  }
}

async function fetchAndRenderTargets() {
  status.textContent = "Loading targets…";

  try {
    const fromSystem = fromSystemInput.value.trim();
    const params = {};
    if (fromSystem) {
      params.from_system = fromSystem;
    }

    const systems = await fetchTargets(params);
    systems.sort((a, b) => (sortDescending ? b.score - a.score : a.score - b.score));
    currentTargets = systems;
    resultsCount.textContent = systems.length.toString();
    renderTargets(systems, { getRowCells });

    status.textContent = systems.length
      ? `Showing ${systems.length} systems${fromSystem ? ` · from ${fromSystem} · route_jumps applied` : ""} · updated ${new Date().toLocaleTimeString()}`
      : fromSystem
      ? `No targets available from ${fromSystem}.`
      : "No targets available.";
  } catch (error) {
    status.textContent = "Failed to load targets.";
    resultsCount.textContent = "0";
    console.error(error);
  }
}

function toggleSort() {
  sortDescending = !sortDescending;
  updateScoreHeader();
  fetchAndRenderTargets();
}

attachRowClickHandler(handleTargetSelection);
initModal();
refreshBtn.addEventListener("click", fetchAndRenderTargets);
fromSystemInput.addEventListener("change", fetchAndRenderTargets);
scoreHeader.addEventListener("click", toggleSort);
updateScoreHeader();
fetchAndRenderTargets();
setInterval(fetchAndRenderTargets, 30000);
