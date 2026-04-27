import { fetchTargets } from "./api.js";
import { renderTargets, attachRowClickHandler } from "./table.js";
import { initModal, openTargetModal } from "./modal.js";

const status = document.getElementById("status");
const refreshBtn = document.getElementById("refreshBtn");
const fromSystemInput = document.getElementById("fromSystem");
const maxDistanceInput = document.getElementById("maxDistance");
const resultsCount = document.getElementById("resultsCount");

let currentTargets = [];
let hasSearched = false;
let refreshTimer = null;

const nearbyColumns = [
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

function handleTargetSelection(index) {
  const target = currentTargets[index];
  if (target) {
    openTargetModal(target);
  }
}

function scheduleRefresh() {
  if (refreshTimer || !hasSearched) {
    return;
  }
  refreshTimer = setInterval(fetchNearbyTargets, 30000);
}

async function fetchNearbyTargets() {
  const fromSystem = fromSystemInput.value.trim();
  if (!fromSystem) {
    status.textContent = "Please enter a current system.";
    resultsCount.textContent = "0";
    return;
  }

  status.textContent = "Loading nearby targets…";

  try {
    const params = { from_system: fromSystem };
    const maxDistance = maxDistanceInput.value.trim();
    if (maxDistance) {
      params.max_distance = maxDistance;
    }

    const systems = await fetchTargets(params);
    systems.sort((a, b) => b.score - a.score);
    currentTargets = systems;
    resultsCount.textContent = systems.length.toString();
    renderTargets(systems, { columns: nearbyColumns });
    status.textContent = systems.length
      ? `Showing ${systems.length} nearby targets · updated ${new Date().toLocaleTimeString()}`
      : "No nearby targets available for the selected parameters.";
    hasSearched = true;
    scheduleRefresh();
  } catch (error) {
    status.textContent = "Failed to load nearby targets.";
    resultsCount.textContent = "0";
    console.error(error);
  }
}

attachRowClickHandler(handleTargetSelection);
initModal();
refreshBtn.addEventListener("click", fetchNearbyTargets);
fromSystemInput.addEventListener("change", () => {
  if (hasSearched) {
    fetchNearbyTargets();
  }
});
maxDistanceInput.addEventListener("change", () => {
  if (hasSearched) {
    fetchNearbyTargets();
  }
});
fetchNearbyTargets();
