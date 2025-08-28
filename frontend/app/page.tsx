"use client";
import { useState } from "react";
import axios from "axios";

export default function Home() {
  const [year, setYear] = useState("2024");
  const [round, setRound] = useState("7");
  const [pitLaps, setPitLaps] = useState("20,35");
  const [laps, setLaps] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);

  async function fetchSim() {
    try {
      setLoading(true);

      const res = await axios.get(
        `http://127.0.0.1:8000/api/simulate?year=${year}&round=${round}&pit_laps=${pitLaps}`
      );

      setLaps(res.data.laps);
    } catch (err) {
      console.error(err);
      alert("Failed to fetch simulation. Try another race/year.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="p-6 max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">Overtakr Strategy Simulator</h1>

      {/* Form */}
      <div className="space-y-2">
        <input
          type="text"
          value={year}
          onChange={(e) => setYear(e.target.value)}
          className="border p-2 rounded w-full"
          placeholder="Year (e.g., 2024)"
        />
        <input
          type="text"
          value={round}
          onChange={(e) => setRound(e.target.value)}
          className="border p-2 rounded w-full"
          placeholder="Round number (e.g., 7)"
        />
        <input
          type="text"
          value={pitLaps}
          onChange={(e) => setPitLaps(e.target.value)}
          className="border p-2 rounded w-full"
          placeholder="Pit stop laps (e.g., 20,35)"
        />
        <button
          onClick={fetchSim}
          disabled={loading}
          className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
        >
          {loading ? "Simulating..." : "Run Simulation"}
        </button>
      </div>

      {/* Results */}
      <div className="mt-6">
        {laps.length > 0 && (
          <div>
            <h2 className="text-xl font-semibold mb-2">Simulated Laps</h2>
            <ul className="space-y-1 max-h-64 overflow-y-auto border p-2 rounded">
              {laps.map((lap, i) => {
                const num = typeof lap === "number" ? lap : parseFloat(lap);
                return (
                  <li key={i}>
                    Lap {i + 1}: {num.toFixed(3)} sec
                  </li>
                );
              })}
            </ul>
          </div>
        )}
      </div>
    </main>
  );
}
