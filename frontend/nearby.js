const API_BASE = "http://localhost:8000";
const targetsBody = document.getElementById("targetsBody");
const status = document.getElementById("status");
const refreshBtn = document.getElementById("refreshBtn");
const fromSystemInput = document.getElementById("fromSystem");
const maxDistanceInput = document.getElementById("maxDistance");
const resultsCount = document.getElementById("resultsCount");
const modal = document.getElementById("targetModal");
const modalBackdrop = document.getElementById("modalBackdrop");
const modalClose = document.getElementById("modalClose");
const modalFields = {
  systemName: document.getElementById("modalSystemName"),
  systemId: document.getElementById("modalSystemId"),
  regionName: document.getElementById("modalRegionName"),
  constellationName: document.getElementById("modalConstellationName"),
  npcKills: document.getElementById("modalNpcKills"),
  shipKills: document.getElementById("modalShipKills"),
  podKills: document.getElementById("modalPodKills"),
  jumps: document.getElementById("modalJumps"),
  distance: document.getElementById("modalDistance"),
  scoreValue: document.getElementById("modalScoreValue"),
  npcContribution: document.getElementById("modalNpcContribution"),
  efficiencyContribution: document.getElementById("modalEfficiencyContribution"),
  trafficPenalty: document.getElementById("modalTrafficPenalty"),
  pvpPenalty: document.getElementById("modalPvpPenalty"),
  distancePenalty: document.getElementById("modalDistancePenalty"),
  riskLabel: document.getElementById("modalRiskLabel"),
  score: document.getElementById("modalScore"),
};

let refreshTimer = null;
let hasSearched = false;
let currentTargets = [];

function formatValue(value) {
  return value != null && value !== "" ? value : "N/A";
}

function getRiskInfo(target) {
  const shipKills = Number(target.ship_kills || 0);
  const podKills = Number(target.pod_kills || 0);
  const jumps = Number(target.jumps || 0);

  if (shipKills >= 3 || podKills >= 2) {
    return { label: "HIGH", className: "badge--high" };
  }

  if (jumps >= 40 || shipKills >= 1) {
    return { label: "MEDIUM", className: "badge--medium" };
  }

  return { label: "LOW", className: "badge--low" };
}

function getBreakdown(target) {
  const npcKills = Number(target.npc_kills || 0);
  const traffic = Number(target.jumps || 0);
  const shipKills = Number(target.ship_kills || 0);
  const podKills = Number(target.pod_kills || 0);
  const distance = target.distance != null ? Number(target.distance) : null;

  return {
    npcContribution: npcKills * 3,
    efficiencyContribution: (npcKills / Math.max(traffic, 1)) * 25,
    trafficPenalty: traffic * 3,
    pvpPenalty: shipKills * 20 + podKills * 30,
    distancePenalty: distance != null ? distance * 75 : null,
    distance,
  };
}

function openTargetModal(target) {
  const breakdown = getBreakdown(target);
  const riskInfo = getRiskInfo(target);

  modalFields.systemName.textContent = formatValue(target.system_name);
  modalFields.systemId.textContent = formatValue(target.system_id);
  modalFields.regionName.textContent = formatValue(target.region_name);
  modalFields.constellationName.textContent = formatValue(target.constellation_name);
  modalFields.npcKills.textContent = formatValue(target.npc_kills);
  modalFields.shipKills.textContent = formatValue(target.ship_kills);
  modalFields.podKills.textContent = formatValue(target.pod_kills);
  modalFields.jumps.textContent = formatValue(target.jumps);
  modalFields.distance.textContent = target.distance != null ? `${target.distance}` : "N/A";
  modalFields.scoreValue.textContent = target.score != null ? Number(target.score).toFixed(1) : "N/A";
  modalFields.npcContribution.textContent = `NPC activity contribution: ${breakdown.npcContribution.toFixed(1)}`;
  modalFields.efficiencyContribution.textContent = `Efficiency contribution: ${breakdown.efficiencyContribution.toFixed(1)}`;
  modalFields.trafficPenalty.textContent = `Traffic penalty: ${breakdown.trafficPenalty.toFixed(1)}`;
  modalFields.pvpPenalty.textContent = `PvP danger penalty: ${breakdown.pvpPenalty.toFixed(1)}`;
  modalFields.distancePenalty.textContent = breakdown.distance != null
    ? `Distance penalty: ${breakdown.distancePenalty.toFixed(1)}`
    : "Distance penalty: N/A";
  modalFields.riskLabel.textContent = riskInfo.label;
  modalFields.riskLabel.className = `badge ${riskInfo.className}`;
  modalFields.score.textContent = target.score != null ? Number(target.score).toFixed(1) : "N/A";
  modal.classList.remove("hidden");
}

function closeTargetModal() {
  modal.classList.add("hidden");
}

function renderTargets(systems) {
  currentTargets = systems;
  targetsBody.innerHTML = "";
  resultsCount.textContent = systems.length.toString();

  if (systems.length === 0) {
    status.textContent = "No nearby targets available for the selected parameters.";
    return;
  }

  systems.forEach((system, index) => {
    const row = document.createElement("tr");
    row.classList.add("table-row");
    row.dataset.index = index;
    if (index < 5) {
      row.classList.add("top-target");
    }
    row.innerHTML = `
      <td>${formatValue(system.system_name)}</td>
      <td>${formatValue(system.region_name)}</td>
      <td>${formatValue(system.constellation_name)}</td>
      <td>${formatValue(system.distance)}</td>
      <td>${system.score != null ? Number(system.score).toFixed(1) : "N/A"}</td>
      <td>${formatValue(system.npc_kills)}</td>
      <td>${formatValue(system.ship_kills)}</td>
      <td>${formatValue(system.pod_kills)}</td>
      <td>${formatValue(system.jumps)}</td>
    `;
    targetsBody.appendChild(row);
  });

  status.textContent = `Showing ${systems.length} nearby targets · updated ${new Date().toLocaleTimeString()}`;
}

function handleTargetClick(event) {
  const row = event.target.closest("tr");
  if (!row || !row.dataset.index) {
    return;
  }
  const target = currentTargets[Number(row.dataset.index)];
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
    const params = new URLSearchParams();
    params.set("from_system", fromSystem);
    const maxDistance = maxDistanceInput.value.trim();
    if (maxDistance) {
      params.set("max_distance", maxDistance);
    }

    const response = await fetch(`${API_BASE}/targets?${params.toString()}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const systems = await response.json();
    systems.sort((a, b) => b.score - a.score);
    renderTargets(systems);
    hasSearched = true;
    scheduleRefresh();
  } catch (error) {
    status.textContent = "Failed to load nearby targets.";
    resultsCount.textContent = "0";
    console.error(error);
  }
}

targetsBody.addEventListener("click", handleTargetClick);
modalClose.addEventListener("click", closeTargetModal);
modalBackdrop.addEventListener("click", closeTargetModal);
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
