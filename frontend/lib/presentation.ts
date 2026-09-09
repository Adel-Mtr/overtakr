export const STRATEGY_COLORS = ["#d3203f", "#0f66c3", "#159947", "#f2b544", "#0d2a4a", "#c85d16"];

export function formatSeconds(totalSeconds: number): string {
  if (!Number.isFinite(totalSeconds)) return "-";
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toFixed(3).padStart(6, "0")}`;
}

