const targetsBody = document.getElementById("targetsBody");

let rowClickHandler = null;

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

export function renderTargets(targets, { getRowCells, topCount = 5 }) {
  targetsBody.innerHTML = "";

  targets.forEach((target, index) => {
    const row = document.createElement("tr");
    row.classList.add("table-row");
    if (index < topCount) {
      row.classList.add("top-target");
    }
    row.dataset.index = index;

    const cells = getRowCells(target);
    row.innerHTML = cells.map((cell) => `<td>${cell}</td>`).join("");
    targetsBody.appendChild(row);
  });
}
