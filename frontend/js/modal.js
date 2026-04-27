import { getBreakdown, getRiskInfo } from "./scoring.js";

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

function formatValue(value) {
  return value != null && value !== "" ? String(value) : "N/A";
}

export function initModal() {
  modalClose.addEventListener("click", closeTargetModal);
  modalBackdrop.addEventListener("click", closeTargetModal);
}

export function openTargetModal(target) {
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
  modalFields.distance.textContent = target.distance != null ? String(target.distance) : "N/A";
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

export function closeTargetModal() {
  modal.classList.add("hidden");
}
