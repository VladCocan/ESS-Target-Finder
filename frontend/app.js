const API_BASE = "http://localhost:8000";
const targetsBody = document.getElementById("targetsBody");
const status = document.getElementById("status");
const refreshBtn = document.getElementById("refreshBtn");
const fromSystemInput = document.getElementById("fromSystem");
const scoreHeader = document.getElementById("scoreHeader");

let sortDescending = true;

function updateScoreHeader() {
  scoreHeader.textContent = `score ${sortDescending ? "▼" : "▲"}`;
}

function renderTargets(systems, fromSystem) {
  targetsBody.innerHTML = "";

  if (systems.length === 0) {
    status.textContent = fromSystem
      ? `No targets available from ${fromSystem}.`
      : "No targets available.";
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

  status.textContent = `Showing ${systems.length} systems${
    fromSystem ? ` · from ${fromSystem} · route_jumps applied` : ""
  } · updated ${new Date().toLocaleTimeString()}`;
}

async function fetchTargets() {
  status.textContent = "Loading targets…";

  try {
    const params = new URLSearchParams();
    const fromSystem = fromSystemInput.value.trim();
    if (fromSystem) {
      params.set("from_system", fromSystem);
    }

    const response = await fetch(`${API_BASE}/targets?${params.toString()}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const systems = await response.json();
    systems.sort((a, b) => (sortDescending ? b.score - a.score : a.score - b.score));
    renderTargets(systems, fromSystem);
  } catch (error) {
    status.textContent = "Failed to load targets.";
    console.error(error);
  }
}

function toggleSort() {
  sortDescending = !sortDescending;
  updateScoreHeader();
  fetchTargets();
}

refreshBtn.addEventListener("click", fetchTargets);
fromSystemInput.addEventListener("change", fetchTargets);
scoreHeader.addEventListener("click", toggleSort);
updateScoreHeader();
fetchTargets();
setInterval(fetchTargets, 30000);

