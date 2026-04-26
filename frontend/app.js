const API_BASE = "http://localhost:8000";
const targetsBody = document.getElementById("targetsBody");
const status = document.getElementById("status");
const refreshBtn = document.getElementById("refreshBtn");

async function fetchTargets() {
  status.textContent = "Loading targets…";
  targetsBody.innerHTML = "";

  try {
    const response = await fetch(`${API_BASE}/targets`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const systems = await response.json();
    systems.sort((a, b) => b.score - a.score);

    if (systems.length === 0) {
      status.textContent = "No targets available.";
      return;
    }

    systems.forEach((system) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${system.system_name || "Unknown"}</td>
        <td>${system.system_id}</td>
        <td>${system.npc_kills}</td>
        <td>${system.ship_kills}</td>
        <td>${system.pod_kills}</td>
        <td>${system.jumps}</td>
        <td>${system.score.toFixed(1)}</td>
      `;
      targetsBody.appendChild(row);
    });

    status.textContent = `Showing ${systems.length} systems`;
  } catch (error) {
    status.textContent = "Failed to load targets.";
    console.error(error);
  }
}

refreshBtn.addEventListener("click", fetchTargets);
fetchTargets();
