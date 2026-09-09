"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { Area, AreaChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SimulationResponse } from "../lib/api";
import { formatSeconds, STRATEGY_COLORS } from "../lib/presentation";

export function SimulationResults({ simulation }: { simulation: SimulationResponse }) {
  const lapChartData = useMemo(() => {
    if (!simulation) return [];

    const strategyEntries = Object.entries(simulation.strategies);
    const totalLaps = simulation.meta.total_laps;

    return Array.from({ length: totalLaps }, (_, index) => {
      const lap = index + 1;
      const point: Record<string, number> = { lap };

      for (const [strategyName, strategyData] of strategyEntries) {
        point[strategyName] = strategyData.laps[index]?.lap_time ?? 0;
      }

      return point;
    });
  }, [simulation]);

  const gapChartData = useMemo(() => {
    if (!simulation) return [];

    const strategyEntries = Object.entries(simulation.strategies);
    const totalLaps = simulation.meta.total_laps;

    return Array.from({ length: totalLaps }, (_, index) => {
      const lap = index + 1;
      const point: Record<string, number> = { lap };
      const cumulatives = strategyEntries.map(([, strategyData]) => strategyData.laps[index]?.cumulative ?? 0);
      const bestAtLap = Math.min(...cumulatives);

      for (const [strategyName, strategyData] of strategyEntries) {
        point[strategyName] = Number(((strategyData.laps[index]?.cumulative ?? 0) - bestAtLap).toFixed(3));
      }

      return point;
    });
  }, [simulation]);

  return (
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.08 }}
          className="mt-6 grid gap-6"
        >
          <div className="panel p-5 md:p-6">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="display-font text-3xl text-[#12203b] md:text-4xl">Strategy Delta Charts</h2>
              <span className="badge bg-[#0f66c322] text-[#0f66c3]">{simulation.meta.race}</span>
            </div>

            <div className="mt-4 grid gap-6 xl:grid-cols-2">
              <div className="h-[320px] w-full rounded-2xl border border-[#d8d8cf] bg-white p-3">
                <p className="mb-2 text-sm font-semibold">Lap Time Projection</p>
                <ResponsiveContainer>
                  <LineChart data={lapChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e0e0d8" />
                    <XAxis dataKey="lap" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} domain={["dataMin - 1", "dataMax + 1"]} />
                    <Tooltip />
                    <Legend />
                    {Object.keys(simulation.strategies).map((name, index) => (
                      <Line
                        key={name}
                        type="monotone"
                        dataKey={name}
                        stroke={STRATEGY_COLORS[index % STRATEGY_COLORS.length]}
                        strokeWidth={2.3}
                        dot={false}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="h-[320px] w-full rounded-2xl border border-[#d8d8cf] bg-white p-3">
                <p className="mb-2 text-sm font-semibold">Cumulative Gap to Best (s)</p>
                <ResponsiveContainer>
                  <AreaChart data={gapChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e0e0d8" />
                    <XAxis dataKey="lap" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Legend />
                    {Object.keys(simulation.strategies).map((name, index) => (
                      <Area
                        key={name}
                        type="monotone"
                        dataKey={name}
                        stroke={STRATEGY_COLORS[index % STRATEGY_COLORS.length]}
                        fill={STRATEGY_COLORS[index % STRATEGY_COLORS.length]}
                        fillOpacity={0.1}
                        strokeWidth={2}
                      />
                    ))}
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="grid gap-6 xl:grid-cols-[1.1fr_1fr]">
            <div className="panel p-5 md:p-6">
              <h3 className="display-font text-3xl text-[#12203b]">Leaderboard</h3>
              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-[#d8d8cf] text-left">
                      <th className="px-2 py-2">Strategy</th>
                      <th className="px-2 py-2">Total Time</th>
                      <th className="px-2 py-2">Gap</th>
                      <th className="px-2 py-2">Pits</th>
                      <th className="px-2 py-2">Avg Lap</th>
                    </tr>
                  </thead>
                  <tbody>
                    {simulation.leaderboard.map((row, index) => (
                      <tr key={row.name} className="border-b border-[#ece9df]">
                        <td className="px-2 py-2 font-semibold" style={{ color: STRATEGY_COLORS[index % STRATEGY_COLORS.length] }}>
                          {row.name}
                        </td>
                        <td className="px-2 py-2">{formatSeconds(row.total_time)}</td>
                        <td className="px-2 py-2">{row.gap_to_best.toFixed(3)}s</td>
                        <td className="px-2 py-2">{row.pits}</td>
                        <td className="px-2 py-2">{row.avg_lap.toFixed(3)}s</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="panel p-5 md:p-6">
              <h3 className="display-font text-3xl text-[#12203b]">Stint Blueprint</h3>
              <p className="mt-1 text-sm subtle">Tyre stint structure for each strategy.</p>

              <div className="mt-4 space-y-4">
                {Object.entries(simulation.strategies).map(([name, strategy], index) => (
                  <div key={name} className="panel-muted p-3">
                    <p className="text-sm font-semibold" style={{ color: STRATEGY_COLORS[index % STRATEGY_COLORS.length] }}>
                      {name}
                    </p>
                    <div className="mt-2 flex min-h-8 overflow-hidden rounded-lg border border-[#dad8ce]">
                      {strategy.stints.map((stint) => {
                        const widthPct = Math.max(6, (stint.laps / simulation.meta.total_laps) * 100);
                        const shade = stint.compound === "SOFT" ? "#ffd1db" : stint.compound === "MEDIUM" ? "#fff0c5" : "#d7e3f3";
                        return (
                          <div
                            key={`${name}-${stint.start_lap}-${stint.compound}`}
                            className="flex items-center justify-center border-r border-[#fff] text-[11px] font-semibold"
                            style={{ width: `${widthPct}%`, background: shade }}
                          >
                            {stint.compound} {stint.start_lap}-{stint.end_lap}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </motion.section>
  );
}
