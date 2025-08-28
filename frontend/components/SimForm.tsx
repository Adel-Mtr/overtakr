'use client';

import { useState } from 'react';

export type SimParams = {
  year: number;
  round: number;
  pitLaps: number[];
};

type Props = {
  onSubmit: (params: SimParams) => void;
  loading?: boolean;
};

function parsePitLaps(input: string): number[] {
  if (!input.trim()) return [];
  return input
    .split(',')
    .map(s => s.trim())
    .filter(Boolean)
    .map(Number)
    .filter(n => Number.isFinite(n) && n > 0);
}

export default function SimForm({ onSubmit, loading }: Props) {
  const [year, setYear] = useState<number>(2023);
  const [round, setRound] = useState<number>(5);
  const [pit, setPit] = useState<string>('20,35');

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({ year, round, pitLaps: parsePitLaps(pit) });
      }}
      className="flex flex-col gap-4 bg-gray-800 p-4 rounded-2xl shadow-lg"
    >
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm text-gray-300 mb-1">Year</label>
          <select
            className="w-full bg-gray-900 border border-gray-700 rounded-xl px-3 py-2"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
          >
            {[2022, 2023, 2024].map(y => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm text-gray-300 mb-1">Round</label>
          <input
            type="number"
            className="w-full bg-gray-900 border border-gray-700 rounded-xl px-3 py-2"
            value={round}
            min={1}
            onChange={(e) => setRound(Number(e.target.value))}
          />
        </div>

        <div>
          <label className="block text-sm text-gray-300 mb-1">Pit Laps (comma-separated)</label>
          <input
            type="text"
            placeholder="e.g. 20,35"
            className="w-full bg-gray-900 border border-gray-700 rounded-xl px-3 py-2"
            value={pit}
            onChange={(e) => setPit(e.target.value)}
          />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={loading}
          className="bg-teal-500 hover:bg-teal-400 disabled:opacity-60 text-black font-semibold px-4 py-2 rounded-xl"
        >
          {loading ? 'Simulating…' : 'Simulate'}
        </button>
        <span className="text-xs text-gray-400">
          Tip: start with a known past race, e.g. 2023 / Round 5 (Spain)
        </span>
      </div>
    </form>
  );
}
