"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DriverDigest, OvertakeMapResponse } from "../lib/api";

type RaceInsightsProps = {
  digest: DriverDigest | null;
  overtake: OvertakeMapResponse | null;
};

export function RaceInsights({ digest, overtake }: RaceInsightsProps) {
  const overtakeChartData = useMemo(() => {
    if (!overtake) return [];

    const lapMap = new Map<number, number>();

    for (const event of overtake.lap_events) {
      lapMap.set(event.lap, (lapMap.get(event.lap) ?? 0) + event.gain);
    }

    return Array.from(lapMap.entries())
      .map(([lap, netChange]) => ({ lap, netChange }))
      .sort((a, b) => a.lap - b.lap);
  }, [overtake]);

  return (
      <section className="mt-6 grid gap-6 xl:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="panel p-5 md:p-6"
        >
          <h2 className="display-font text-3xl text-[#12203b] md:text-4xl">Driver Digest</h2>
          {!digest && <p className="mt-3 text-sm subtle">Run analysis to generate a personalized race story.</p>}
          {digest && (
            <>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <div className="panel-muted p-3">
                  <p className="text-xs uppercase tracking-[0.08em] subtle">Driver</p>
                  <p className="mt-1 text-lg font-bold">{digest.driver} - {digest.full_name}</p>
                  <p className="text-sm subtle">{digest.team}</p>
                </div>
                <div className="panel-muted p-3">
                  <p className="text-xs uppercase tracking-[0.08em] subtle">Position Swing</p>
                  <p className="mt-1 text-lg font-bold">
                    P{digest.grid_position} to P{digest.finish_position}
                  </p>
                  <p className="text-sm subtle">Net {digest.places_gained >= 0 ? `+${digest.places_gained}` : digest.places_gained}</p>
                </div>
                <div className="panel-muted p-3">
                  <p className="text-xs uppercase tracking-[0.08em] subtle">Best Lap</p>
                  <p className="mt-1 text-lg font-bold">
                    {digest.best_lap ? `Lap ${digest.best_lap.lap}` : "-"}
                  </p>
                  <p className="text-sm subtle">{digest.best_lap ? `${digest.best_lap.time.toFixed(3)}s` : "No valid best lap"}</p>
                </div>
                <div className="panel-muted p-3">
                  <p className="text-xs uppercase tracking-[0.08em] subtle">Consistency</p>
                  <p className="mt-1 text-lg font-bold">{digest.consistency_std.toFixed(3)}s</p>
                  <p className="text-sm subtle">Average lap {digest.average_lap.toFixed(3)}s</p>
                </div>
              </div>

              <div className="panel-muted mt-4 p-4">
                <p className="text-xs uppercase tracking-[0.08em] subtle">Storyline</p>
                <p className="mt-2 text-sm text-[#2d3650]">{digest.storyline}</p>
              </div>

              <div className="mt-4 space-y-2">
                {digest.stints.map((stint, index) => (
                  <div key={`${stint.compound}-${index}`} className="flex items-center justify-between rounded-xl border border-[#ddd8cd] bg-white px-3 py-2 text-sm">
                    <span className="font-semibold">{stint.compound}</span>
                    <span className="subtle">
                      Lap {stint.start_lap} to {stint.end_lap} ({stint.laps} laps)
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.14 }}
          className="panel p-5 md:p-6"
        >
          <h2 className="display-font text-3xl text-[#12203b] md:text-4xl">Overtake Intelligence</h2>
          {!overtake && <p className="mt-3 text-sm subtle">Run analysis to inspect position-change momentum.</p>}
          {overtake && (
            <>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <div className="panel-muted p-3">
                  <p className="text-xs uppercase tracking-[0.08em] subtle">Position Changes</p>
                  <p className="mt-1 text-lg font-bold">{overtake.summary.total_position_changes}</p>
                </div>
                <div className="panel-muted p-3">
                  <p className="text-xs uppercase tracking-[0.08em] subtle">Most Active Lap</p>
                  <p className="mt-1 text-lg font-bold">{overtake.summary.most_active_lap ?? "-"}</p>
                </div>
              </div>

              <div className="mt-4 h-[250px] rounded-2xl border border-[#d8d8cf] bg-white p-3">
                <ResponsiveContainer>
                  <BarChart data={overtakeChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e0e0d8" />
                    <XAxis dataKey="lap" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="netChange" fill="#0f66c3" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="panel-muted mt-4 p-4">
                <p className="text-xs uppercase tracking-[0.08em] subtle">Final Position Swings</p>
                <div className="mt-2 space-y-2">
                  {overtake.driver_swings.slice(0, 8).map((item) => (
                    <div key={item.driver} className="flex items-center justify-between rounded-xl border border-[#ddd8cd] bg-white px-3 py-2 text-sm">
                      <span className="font-semibold">{item.driver}</span>
                      <span className="subtle">
                        P{item.grid} to P{item.finish} ({item.net >= 0 ? `+${item.net}` : item.net})
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </motion.div>
      </section>
  );
}
