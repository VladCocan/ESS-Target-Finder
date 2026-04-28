import { fetchTargets } from "./api.js";
import { renderTargets, attachRowClickHandler } from "./table.js";
import { initModal, openTargetModal } from "./modal.js";

const status = document.getElementById("status");
const refreshBtn = document.getElementById("refreshBtn");
const useCurrentLocationBtn = document.getElementById("useCurrentLocationBtn");
const fromSystemInput = document.getElementById("fromSystem");
const maxDistanceInput = document.getElementById("maxDistance");
const resultsCount = document.getElementById("resultsCount");
const authDetails = document.getElementById("authDetails");
const loginButton = document.getElementById("loginButton");
const logoutButton = document.getElementById("logoutButton");

let currentTargets = [];
let manualOverride = false;

async function fetchAuthMe() {
  try {
    const response = await fetch("/api/auth/me", { credentials: "include" });
    if (!response.ok) {
      return null;
    }
    return response.json();
  } catch (error) {
    console.error("Unable to fetch auth status", error);
    return null;
  }
}

async function fetchAuthLocation() {
  try {
    const response = await fetch("/api/auth/location", {
      credentials: "include",
    });
    if (!response.ok) {
      if (response.status === 401) {
        setAuthState(null);
      }
      throw new Error("Unable to retrieve current location");
    }
    return response.json();
  } catch (error) {
    console.error("Unable to fetch auth location", error);
    throw error;
  }
}

async function resolveSystemName(systemId) {
  if (!systemId) {
    return null;
  }

  try {
    const response = await fetch(
      "https://esi.evetech.net/latest/universe/names/?datasource=tranquility",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify([systemId]),
      }
    );
    if (!response.ok) {
      throw new Error("Unable to resolve system name");
    }
    const names = await response.json();
    const match = names.find((item) => item.id === systemId);
    return match?.name ?? null;
  } catch (error) {
    console.error("Unable to resolve system name", error);
    return null;
  }
}

function setAuthState(user, locationData) {
  if (user) {
    authDetails.style.display = "block";
    authDetails.textContent = `Signed in as ${user.character_name}`;
    if (locationData && locationData.solar_system_id) {
      const locationText = locationData.system_name || locationData.solar_system_id;
      const locationLabel = document.createElement("button");
      locationLabel.type = "button";
      locationLabel.className = "auth-location-link";
      locationLabel.textContent = locationText;
      locationLabel.dataset.systemName = locationText;
      authDetails.append(document.createTextNode(" · location "));
      authDetails.append(locationLabel);
    }
    loginButton.style.display = "none";
    logoutButton.style.display = "inline-flex";
  } else {
    authDetails.style.display = "none";
    authDetails.textContent = "";
    loginButton.style.display = "inline-flex";
    logoutButton.style.display = "none";
  }
}

async function logout() {
  try {
    const response = await fetch("/api/auth/logout", {
      method: "POST",
      credentials: "include",
    });
    if (response.ok) {
      setAuthState(null);
    }
  } catch (error) {
    console.error("Logout failed", error);
  }
}

async function loadAuthState() {
  const user = await fetchAuthMe();
  if (!user) {
    setAuthState(null);
    return;
  }

  let locationData = null;
  let locationError = false;
  try {
    locationData = await fetchAuthLocation();
  } catch (error) {
    locationError = true;
  }

  if (locationData?.solar_system_id && !locationData.system_name) {
    const resolved = await resolveSystemName(locationData.solar_system_id);
    if (resolved) {
      locationData.system_name = resolved;
    }
  }

  setAuthState(user, locationData);

  if (locationData) {
    const systemName = locationData.system_name;
    if (systemName) {
      setFromSystemValue(systemName, { force: false });
    }
  }

  if (locationError) {
    status.textContent =
      "Unable to load current location. Manual search still works.";
  }
}

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

async function openLocationTarget(systemName) {
  if (!systemName) {
    return;
  }

  const findTarget = () =>
    currentTargets.find(
      (item) => item.system_name?.toLowerCase() === systemName.toLowerCase()
    );

  let target = findTarget();
  if (!target) {
    if (!hasSearched) {
      await fetchNearbyTargets();
      target = findTarget();
    }
  }

  if (target) {
    openTargetModal(target);
  } else {
    status.textContent = `No target details available for ${systemName}.`;
  }
}

function setFromSystemValue(value, { force = false } = {}) {
  if (!value) {
    return;
  }
  if (!manualOverride || force) {
    fromSystemInput.value = value;
    if (force) {
      manualOverride = false;
    }
  }
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
useCurrentLocationBtn.addEventListener("click", async () => {
  try {
    status.textContent = "Loading current location…";
    const locationData = await fetchAuthLocation();
    if (locationData?.solar_system_id && !locationData.system_name) {
      const resolved = await resolveSystemName(locationData.solar_system_id);
      if (resolved) {
        locationData.system_name = resolved;
      }
    }
    const systemName = locationData?.system_name;
    if (systemName) {
      setFromSystemValue(systemName, { force: true });
      await fetchNearbyTargets();
    } else {
      status.textContent =
        "Current location could not be resolved. Please enter a system manually.";
    }
  } catch (error) {
    status.textContent =
      "Unable to load current location. Please enter a system manually or log in again.";
  }
});
fromSystemInput.addEventListener("input", () => {
  manualOverride = true;
});
authDetails.addEventListener("click", async (event) => {
  const button = event.target.closest(".auth-location-link");
  if (!button) {
    return;
  }
  await openLocationTarget(button.dataset.systemName);
});
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
logoutButton.addEventListener("click", async () => {
  await logout();
});

(async function initPage() {
  status.textContent = "Checking EVE login…";
  await loadAuthState();
  await fetchNearbyTargets();
})();
