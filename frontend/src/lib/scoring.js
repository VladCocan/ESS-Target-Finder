export function getRiskInfo(target) {
  const shipKills = Number(target.ship_kills || 0)
  const podKills = Number(target.pod_kills || 0)
  const jumps = Number(target.jumps || 0)

  if (shipKills >= 3 || podKills >= 2) {
    return { label: 'HIGH', className: 'badge--high' }
  }

  if (jumps >= 40 || shipKills >= 1) {
    return { label: 'MEDIUM', className: 'badge--medium' }
  }

  return { label: 'LOW', className: 'badge--low' }
}

export function getScoreBreakdown(target) {
  const npcKills = Number(target.npc_kills || 0)
  const traffic = Number(target.jumps || 0)
  const shipKills = Number(target.ship_kills || 0)
  const podKills = Number(target.pod_kills || 0)
  const distance = target.distance != null ? Number(target.distance) : null

  return {
    npcContribution: npcKills * 3,
    efficiencyContribution: (npcKills / Math.max(traffic, 1)) * 25,
    trafficPenalty: traffic * 3,
    pvpPenalty: shipKills * 20 + podKills * 30,
    distancePenalty: distance != null ? distance * 75 : null,
    distance,
  }
}
