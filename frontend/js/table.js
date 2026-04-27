const targetsBody = document.getElementById("targetsBody");

let rowClickHandler = null;

function formatValue(value) {
  return value != null && value !== "" ? String(value) : "N/A";
}

function formatCell(column, target) {
  if (column === "score") {
    return target.score != null ? Number(target.score).toFixed(1) : "N/A";
  }

  return formatValue(target[column]);
}

export function attachRowClickHandler(handler) {
  rowClickHandler = handler;
  targetsBody.addEventListener("click", (event) => {
    const row = event.target.closest("tr");
    if (!row || !row.dataset.index) {
      return;
    }
    rowClickHandler(Number(row.dataset.index));
  });
}

export function renderTargets(targets, { columns, topCount = 5 }) {
  targetsBody.innerHTML = "";

  targets.forEach((target, index) => {
    const row = document.createElement("tr");
    row.classList.add("table-row");
    if (index < topCount) {
      row.classList.add("top-target");
    }
    row.dataset.index = index;

    const cells = columns.map((column) => formatCell(column, target));
    row.innerHTML = cells.map((cell) => `<td>${cell}</td>`).join("");
    targetsBody.appendChild(row);
  });
}
