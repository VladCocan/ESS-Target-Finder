const API_BASE = "http://localhost:8000";
const targetsBody = document.getElementById("targetsBody");
const status = document.getElementById("status");
const refreshBtn = document.getElementById("refreshBtn");
const fromSystemInput = document.getElementById("fromSystem");
const maxDistanceInput = document.getElementById("maxDistance");
const resultsCount = document.getElementById("resultsCount");

let refreshTimer = null;
let hasSearched = false;

function renderTargets(systems) {
  targetsBody.innerHTML = "";
  resultsCount.textContent = systems.length.toString();

  if (systems.length === 0) {
    status.textContent = "No nearby targets available for the selected parameters.";
    return;
  }

  systems.forEach((system, index) => {
    const row = document.createElement("tr");
    if (index < 5) {
      row.classList.add("top-target");
    }
    row.innerHTML = `
      <td>${system.system_name || "Unknown"}</td>
      <td>${system.region_name || "Unknown"}</td>
      <td>${system.constellation_name || "Unknown"}</td>
      <td>${system.system_id}</td>
      <td>${system.npc_kills}</td>
      <td>${system.ship_kills}</td>
      <td>${system.pod_kills}</td>
      <td>${system.jumps}</td>
      <td>${system.distance ?? 0}</td>
      <td>${Number(system.score).toFixed(1)}</td>
    `;
    targetsBody.appendChild(row);
  });

  status.textContent = `Showing ${systems.length} nearby targets · updated ${new Date().toLocaleTimeString()}`;
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
