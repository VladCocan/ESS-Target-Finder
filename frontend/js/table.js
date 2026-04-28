const targetsBody = document.getElementById("targetsBody");

let rowClickHandler = null;
let currentTargets = [];
let renderOptions = null;
const STORAGE_KEY = "savedTargets";

function formatValue(value) {
  return value != null && value !== "" ? String(value) : "N/A";
}

function getSavedTargets() {
  const saved = localStorage.getItem(STORAGE_KEY);
  try {
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
}

function setSavedTargets(targets) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(targets));
}

function isSaved(target) {
  const saved = getSavedTargets();
  return saved.some((item) => item.system_id === target.system_id);
}

function formatCell(column, target) {
  if (column === "score") {
    return target.score != null ? Number(target.score).toFixed(1) : "N/A";
  }

  return formatValue(target[column]);
}

function getHeaderActions() {
  const table = targetsBody.closest("table");
  if (!table) {
    return [];
  }

  return Array.from(table.querySelectorAll("thead th"))
    .map((th) => th.textContent.trim().toLowerCase())
    .filter((label) => label === "save" || label === "remove");
}

function renderActionButton(action, target) {
  if (action === "save") {
    const saved = isSaved(target);
    return `<button type="button" class="btn btn--secondary btn--sm js-save-button" ${saved ? "disabled" : ""}>${saved ? "Saved" : "Save"}</button>`;
  }

  if (action === "remove") {
    return `<button type="button" class="btn btn--danger btn--sm js-remove-button">Remove</button>`;
  }

  return "";
}

function dispatchSavedTargetsUpdated() {
  window.dispatchEvent(new CustomEvent("savedTargetsUpdated", { detail: { targets: currentTargets } }));
}

function saveTarget(target, button) {
  if (!target || !target.system_id) {
    return;
  }

  const saved = getSavedTargets();
  if (saved.some((item) => item.system_id === target.system_id)) {
    return;
  }

  saved.push(target);
  setSavedTargets(saved);

  if (button) {
    button.textContent = "Saved";
    button.disabled = true;
  }
}

function removeTarget(target) {
  if (!target || !target.system_id) {
    return;
  }

  const saved = getSavedTargets();
  const remaining = saved.filter((item) => item.system_id !== target.system_id);
  setSavedTargets(remaining);

  if (renderOptions) {
    currentTargets = currentTargets.filter((item) => item.system_id !== target.system_id);
    renderTargets(currentTargets, renderOptions);
    dispatchSavedTargetsUpdated();
  }
}

function handleActionClick(event) {
  const button = event.target.closest("button");
  if (!button) {
    return false;
  }

  const row = button.closest("tr");
  if (!row || !row.dataset.index) {
    return false;
  }

  const target = currentTargets[Number(row.dataset.index)];
  if (!target) {
    return false;
  }

  if (button.classList.contains("js-save-button")) {
    saveTarget(target, button);
    return true;
  }

  if (button.classList.contains("js-remove-button")) {
    removeTarget(target);
    return true;
  }

  return false;
}

export function attachRowClickHandler(handler) {
  rowClickHandler = handler;
  targetsBody.addEventListener("click", (event) => {
    if (handleActionClick(event)) {
      return;
    }

    const row = event.target.closest("tr");
    if (!row || !row.dataset.index) {
      return;
    }

    rowClickHandler(Number(row.dataset.index));
  });
}

export function renderTargets(targets, { columns, topCount = 5 }) {
  currentTargets = Array.isArray(targets) ? targets.slice() : [];
  renderOptions = { columns, topCount };
  targetsBody.innerHTML = "";

  const actionHeaders = getHeaderActions();

  currentTargets.forEach((target, index) => {
    const row = document.createElement("tr");
    row.classList.add("table-row");
    if (index < topCount) {
      row.classList.add("top-target");
    }
    row.dataset.index = index;

    const cells = columns.map((column) => formatCell(column, target));
    const actionCells = actionHeaders.map((action) => renderActionButton(action, target));
    row.innerHTML = [...cells, ...actionCells].map((cell) => `<td>${cell}</td>`).join("");
    targetsBody.appendChild(row);
  });
}
