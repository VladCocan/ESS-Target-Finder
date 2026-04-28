import { renderTargets, attachRowClickHandler } from "./table.js";
import { initModal, openTargetModal } from "./modal.js";

const status = document.getElementById("status");
const clearSavedBtn = document.getElementById("clearSavedBtn");
const resultsCount = document.getElementById("resultsCount");

const savedColumns = [
  "system_name",
  "region_name",
  "constellation_name",
  "distance",
  "score",
  "npc_kills",
  "ship_kills",
  "pod_kills",
  "jumps",
];

function loadSavedTargets() {
  const saved = localStorage.getItem("savedTargets");
  try {
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
}

function saveTargets(targets) {
  localStorage.setItem("savedTargets", JSON.stringify(targets));
}

function renderSavedTargets() {
  const targets = loadSavedTargets();
  resultsCount.textContent = targets.length.toString();
  status.textContent = targets.length
    ? `Showing ${targets.length} saved targets.`
    : "No saved targets yet.";

  renderTargets(targets, { columns: savedColumns, topCount: targets.length });
}

function handleTargetSelection(index) {
  const targets = loadSavedTargets();
  const target = targets[index];
  if (target) {
    openTargetModal(target);
  }
}

function clearSaved() {
  saveTargets([]);
  renderSavedTargets();
}

attachRowClickHandler(handleTargetSelection);
initModal();
clearSavedBtn.addEventListener("click", clearSaved);
window.addEventListener("savedTargetsUpdated", renderSavedTargets);
renderSavedTargets();
