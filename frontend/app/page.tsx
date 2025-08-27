'use client'

import React, { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  ResponsiveContainer
} from "recharts";
import axios from "axios";

interface LapData {
  lap: number;
  actual: number;
  scenario: number;
}

export default function Home() {
  const [laps, setLaps] = useState<LapData[]>([]);

  useEffect(() => {
    async function fetchSim() {
      try {
        const res = await axios.post("http://localhost:8000/api/simulate");
        setLaps(res.data.laps);
      } catch (err) {
        console.error("Failed to fetch simulation", err);
      }
    }
    fetchSim();
  }, []);

  return (
    <main className="min-h-screen p-8">
      <h1 className="text-3xl font-bold mb-6 text-teal-400">Overtakr — Strategy Visualizer</h1>
      <div className="bg-gray-800 p-4 rounded-2xl shadow-lg">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={laps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#555" />
            <XAxis dataKey="lap" stroke="#fff" />
            <YAxis stroke="#fff" />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="actual" stroke="#00f" strokeWidth={2} />
            <Line type="monotone" dataKey="scenario" stroke="#0f0" strokeWidth={2} strokeDasharray="5 5" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </main>
  );
}
