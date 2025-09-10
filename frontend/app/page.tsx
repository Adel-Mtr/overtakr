"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { ReferenceLine } from "recharts";

export default function Home() {
  const [year, setYear] = useState(2024);
  const [round, setRound] = useState(7);
  const [strategies, setStrategies] = useState([
    { name: "Strat A", pit_laps: "20,35" },
  ]);
  type SimResults = Record<string, number[]>; // { "Strat A": [93.2, 92.5, ...], ... }
  const [results, setResults] = useState<SimResults | null>(null);
  const [races, setRaces] = useState<{ round: number; name: string }[]>([]);
  const [drivers, setDrivers] = useState<string[]>([]);

  useEffect(() => {
    async function loadRaces() {
      try {
        const res = await axios.get("http://127.0.0.1:8000/api/races", {
          params: { year },
        });
        setRaces(res.data);
        if (res.data.length > 0) {
          setRound(res.data[0].round); // default to first race
        }
      } catch (err) {
        console.error("Failed to fetch races", err);
      }
    }
    loadRaces();
  }, [year]);

  useEffect(() => {
    async function loadDrivers() {
      try {
        const res = await axios.get("http://127.0.0.1:8000/api/drivers", {
          params: { year, round },
        });
        setDrivers(res.data);
      } catch (err) {
        console.error("Failed to fetch drivers", err);
      }
    }
    if (round) loadDrivers();
  }, [year, round]);

  async function fetchSim() {
    try {
      const res = await axios.post("http://127.0.0.1:8000/api/simulate", {
        year,
        round,
        strategies,
      });
      setResults(res.data.strategies);
    } catch (err) {
      console.error("Failed to fetch simulation", err);
    }
  }

  function addStrategy() {
    setStrategies([
      ...strategies,
      {
        name: `Strat ${String.fromCharCode(65 + strategies.length)}`,
        pit_laps: "",
      },
    ]);
  }

  // Build chart data: each row = lap, each key = strategy
  const chartData = results
    ? Object.keys(results[Object.keys(results)[0]]).map((_, i) => {
        const row: Record<string, number> = { lap: i + 1 };
        for (const strat in results) {
          row[strat] = parseFloat(results[strat][i]);
        }
        return row;
      })
    : [];

  return (
    <main className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Overtakr – Strategy Simulator</h1>

      <div className="flex gap-4 mb-4">
        <input
          type="number"
          value={year}
          onChange={(e) => setYear(Number(e.target.value))}
          className="border p-2 rounded w-24"
        />
        <select
          value={round}
          onChange={(e) => setRound(Number(e.target.value))}
          className="border p-2 rounded"
        >
          {races.map((r) => (
            <option key={r.round} value={String(r.round)}>
              {r.round}. {r.name}
            </option>
          ))}
        </select>
        <select
          className="border p-2 rounded"
          onChange={(e) => console.log("Selected driver:", e.target.value)}
        >
          <option value="">All Drivers</option>
          {drivers.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
        <button
          onClick={addStrategy}
          className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
        >
          + Add Strategy
        </button>
        <button
          onClick={fetchSim}
          className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
        >
          Simulate
        </button>
      </div>

      <div className="space-y-3">
        {strategies.map((s, idx) => (
          <div
            key={idx}
            className="flex items-center gap-2 bg-neutral-800 p-3 rounded-xl shadow"
          >
            <input
              type="text"
              value={s.name}
              onChange={(e) => {
                const newStrats = [...strategies];
                newStrats[idx].name = e.target.value;
                setStrategies(newStrats);
              }}
              className="bg-neutral-900 text-white border border-neutral-700 rounded px-2 py-1 w-28"
            />
            <input
              type="text"
              value={s.pit_laps}
              onChange={(e) => {
                const newStrats = [...strategies];
                newStrats[idx].pit_laps = e.target.value;
                setStrategies(newStrats);
              }}
              placeholder="e.g. 20,35"
              className="bg-neutral-900 text-white border border-neutral-700 rounded px-2 py-1 flex-1"
            />
            <button
              onClick={() => {
                setStrategies(strategies.filter((_, i) => i !== idx));
              }}
              className="bg-red-700 hover:bg-red-800 text-white px-3 py-1 rounded"
            >
              ✕
            </button>
          </div>
        ))}
      </div>

      {results && (
        <div className="bg-neutral-800 p-4 rounded-xl shadow w-full h-[500px]">
          <ResponsiveContainer>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#444" />
              <XAxis dataKey="lap" stroke="#ccc" />
              <YAxis stroke="#ccc" />
              <Tooltip
                contentStyle={{ backgroundColor: "#222", border: "none" }}
              />
              <Legend />
              {Object.keys(results).map((strat, i) => (
                <Line
                  key={strat}
                  type="monotone"
                  dataKey={strat}
                  stroke={["#ff1e00", "#007bff", "#00c49f", "#ffbb28"][i % 4]}
                  strokeWidth={2}
                  dot={false}
                />
              ))}
              {/* Pit stop reference lines */}
              {strategies.map((s, idx) =>
                s.pit_laps
                  .split(",")
                  .filter((x) => x.trim() !== "")
                  .map((lapStr, j) => (
                    <ReferenceLine
                      key={`${s.name}-pit-${j}`}
                      x={parseInt(lapStr)}
                      stroke={
                        ["#ff1e00", "#007bff", "#00c49f", "#ffbb28"][idx % 4]
                      }
                      strokeDasharray="4 4"
                      label={{
                        value: `${s.name} pit`,
                        position: "top",
                        fill: "#aaa",
                      }}
                    />
                  ))
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </main>
  );
}
