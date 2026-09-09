"use client";

import axios from "axios";
import { SimulationResults } from "../components/SimulationResults";
import { RaceInsights } from "../components/RaceInsights";
import { formatSeconds, STRATEGY_COLORS } from "../lib/presentation";
import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";

import {
  Compound,
  DriverDigest,
  DriverOption,
  OvertakeMapResponse,
  RaceOption,
  SimulationResponse,
  TyreProfile,
  fetchDriverDigest,
  fetchDrivers,
  fetchOvertakeMap,
  fetchRaces,
  fetchYears,
  runSimulation,
} from "../lib/api";

type StrategyDraft = {
  id: string;
  name: string;
  pitLaps: string;
  startCompound: Compound;
  tyreProfile: TyreProfile;
  fuelSave: number;
};

type ScenarioPayload = {
  year: number;
  round: number;
  driver: string | null;
  pitPenalty: number;
  weatherRisk: number;
  strategies: Array<{
    name: string;
    pitLaps: string;
    startCompound: Compound;
    tyreProfile: TyreProfile;
    fuelSave: number;
  }>;
};



function makeStrategy(index: number): StrategyDraft {
  const labels = ["Baseline", "Attack", "Undercut", "Late Charge", "Safety Buffer", "Wildcard"];
  const compounds: Compound[] = ["MEDIUM", "SOFT", "HARD", "MEDIUM", "HARD", "SOFT"];
  const profiles: TyreProfile[] = [
    "balanced",
    "aggressive",
    "conservative",
    "balanced",
    "conservative",
    "aggressive",
  ];

  return {
    id: `strategy-${Date.now()}-${index}`,
    name: labels[index] ?? `Strategy ${index + 1}`,
    pitLaps: ["18,39", "14,31,49", "23", "20,44", "26", "11,28,47"][index] ?? "20,40",
    startCompound: compounds[index] ?? "MEDIUM",
    tyreProfile: profiles[index] ?? "balanced",
    fuelSave: 0,
  };
}


function encodeScenario(payload: ScenarioPayload): string {
  const raw = JSON.stringify(payload);
  const base64 = window.btoa(raw);
  return base64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function decodeScenario(token: string): ScenarioPayload | null {
  try {
    const padded = token.replace(/-/g, "+").replace(/_/g, "/");
    const padLength = (4 - (padded.length % 4)) % 4;
    const base64 = padded + "=".repeat(padLength);
    const payload = JSON.parse(window.atob(base64)) as ScenarioPayload;

    if (!payload || typeof payload !== "object") {
      return null;
    }

    return payload;
  } catch {
    return null;
  }
}

function toErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const apiDetail = (error.response?.data as { detail?: string } | undefined)?.detail;
    return apiDetail ?? error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Unexpected error";
}

export default function Home() {
  const [years, setYears] = useState<number[]>([]);
  const [races, setRaces] = useState<RaceOption[]>([]);
  const [drivers, setDrivers] = useState<DriverOption[]>([]);

  const [year, setYear] = useState<number>(2024);
  const [round, setRound] = useState<number>(7);
  const [driver, setDriver] = useState<string>("");

  const [pitPenalty, setPitPenalty] = useState<number>(21.5);
  const [weatherRisk, setWeatherRisk] = useState<number>(0.15);
  const [strategies, setStrategies] = useState<StrategyDraft[]>([makeStrategy(0), makeStrategy(1)]);

  const [simulation, setSimulation] = useState<SimulationResponse | null>(null);
  const [digest, setDigest] = useState<DriverDigest | null>(null);
  const [overtake, setOvertake] = useState<OvertakeMapResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const scenarioToken = params.get("scenario");
    if (!scenarioToken) {
      return;
    }

    const decoded = decodeScenario(scenarioToken);
    if (!decoded) {
      return;
    }

    setYear(decoded.year);
    setRound(decoded.round);
    setDriver(decoded.driver ?? "");
    setPitPenalty(decoded.pitPenalty);
    setWeatherRisk(decoded.weatherRisk);

    if (decoded.strategies?.length) {
      setStrategies(
        decoded.strategies.slice(0, 6).map((item, index) => ({
          id: `scenario-${index}-${Date.now()}`,
          name: item.name,
          pitLaps: item.pitLaps,
          startCompound: item.startCompound,
          tyreProfile: item.tyreProfile,
          fuelSave: item.fuelSave,
        }))
      );
    }
  }, []);

  useEffect(() => {
    let active = true;

    async function loadYears() {
      try {
        const yearOptions = await fetchYears();
        if (!active) return;

        setYears(yearOptions);
        if (!yearOptions.includes(year)) {
          setYear(yearOptions[0] ?? year);
        }
      } catch (err) {
        if (!active) return;
        setError(`Failed to load available seasons: ${toErrorMessage(err)}`);
      }
    }

    loadYears();

    return () => {
      active = false;
    };
  }, [year]);

  useEffect(() => {
    let active = true;

    async function loadRaces() {
      try {
        const raceOptions = await fetchRaces(year);
        if (!active) return;

        setRaces(raceOptions);

        const selectedStillExists = raceOptions.some((item) => item.round === round);
        if (!selectedStillExists && raceOptions.length > 0) {
          setRound(raceOptions[0].round);
        }
      } catch (err) {
        if (!active) return;
        setError(`Failed to load races for ${year}: ${toErrorMessage(err)}`);
      }
    }

    loadRaces();

    return () => {
      active = false;
    };
  }, [year, round]);

  useEffect(() => {
    if (!round) {
      return;
    }

    let active = true;

    async function loadDrivers() {
      try {
        const driverOptions = await fetchDrivers(year, round);
        if (!active) return;

        setDrivers(driverOptions);

        const selectedStillExists = driverOptions.some((item) => item.code === driver);
        if (!selectedStillExists) {
          setDriver("");
        }
      } catch (err) {
        if (!active) return;
        setError(`Failed to load drivers: ${toErrorMessage(err)}`);
      }
    }

    loadDrivers();

    return () => {
      active = false;
    };
  }, [year, round, driver]);

  const selectedRace = useMemo(
    () => races.find((raceOption) => raceOption.round === round) ?? null,
    [races, round]
  );

  const currentDriver = useMemo(
    () => drivers.find((driverOption) => driverOption.code === driver) ?? null,
    [drivers, driver]
  );

  const topStrategy = simulation?.leaderboard[0] ?? null;

  async function handleRunAnalysis() {
    if (!round || strategies.length === 0) {
      setError("Please select a race and at least one strategy.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const simulationResult = await runSimulation({
        year,
        round,
        ...(driver ? { driver } : {}),
        pit_penalty: Number(pitPenalty.toFixed(1)),
        weather_risk: Number(weatherRisk.toFixed(2)),
        strategies: strategies.map((strategy) => ({
          name: strategy.name.trim() || "Strategy",
          pit_laps: strategy.pitLaps,
          start_compound: strategy.startCompound,
          tyre_profile: strategy.tyreProfile,
          fuel_save: Number(strategy.fuelSave.toFixed(2)),
        })),
      });

      setSimulation(simulationResult);

      const [digestResult, overtakeResult] = await Promise.all([
        fetchDriverDigest(year, round, driver || undefined),
        fetchOvertakeMap(year, round, driver || undefined),
      ]);

      setDigest(digestResult.digest);
      setOvertake(overtakeResult);
    } catch (err) {
      setError(`Analysis failed: ${toErrorMessage(err)}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleCopyScenario() {
    const payload: ScenarioPayload = {
      year,
      round,
      driver: driver || null,
      pitPenalty,
      weatherRisk,
      strategies: strategies.map((strategy) => ({
        name: strategy.name,
        pitLaps: strategy.pitLaps,
        startCompound: strategy.startCompound,
        tyreProfile: strategy.tyreProfile,
        fuelSave: strategy.fuelSave,
      })),
    };

    const encoded = encodeScenario(payload);
    const url = new URL(window.location.href);
    url.searchParams.set("scenario", encoded);

    try {
      await navigator.clipboard.writeText(url.toString());
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      setError("Could not copy scenario URL to clipboard.");
    }
  }

  function updateStrategy(id: string, patch: Partial<StrategyDraft>) {
    setStrategies((prev) => prev.map((item) => (item.id === id ? { ...item, ...patch } : item)));
  }

  function addStrategy() {
    setStrategies((prev) => [...prev, makeStrategy(prev.length)].slice(0, 6));
  }

  function removeStrategy(id: string) {
    setStrategies((prev) => {
      if (prev.length === 1) {
        return prev;
      }
      return prev.filter((item) => item.id !== id);
    });
  }

  return (
    <main className="mx-auto max-w-[1320px] px-4 pb-12 pt-6 md:px-8 md:pt-8 lg:px-12">
      <motion.section
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="panel overflow-hidden p-6 md:p-8"
      >
        <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr] lg:items-end">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#0f66c3]">Formula 1 Intelligence Lab</p>
            <h1 className="display-font mt-3 text-5xl leading-[0.9] text-[#111827] md:text-7xl">
              OVERTAKR
            </h1>
            <p className="mt-3 max-w-2xl text-base text-[#49536b] md:text-lg">
              A portfolio-grade strategy platform for race simulations, pit-window scouting, and driver-level storytelling.
              Build scenarios, compare outcomes, and share exact race setups.
            </p>
          </div>

          <div className="panel-muted p-4 md:p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#5d6680]">Session Snapshot</p>
            <div className="mt-2 grid grid-cols-2 gap-3 text-sm">
              <div>
                <div className="subtle">Race</div>
                <div className="font-semibold">{selectedRace ? `${selectedRace.round}. ${selectedRace.name}` : `Round ${round}`}</div>
              </div>
              <div>
                <div className="subtle">Driver Focus</div>
                <div className="font-semibold">{currentDriver ? currentDriver.code : "Field Benchmark"}</div>
              </div>
              <div>
                <div className="subtle">Scenario Count</div>
                <div className="font-semibold">{strategies.length}</div>
              </div>
              <div>
                <div className="subtle">Status</div>
                <div className="font-semibold">{loading ? "Running" : "Ready"}</div>
              </div>
            </div>
          </div>
        </div>
      </motion.section>

      <section className="mt-6 grid gap-6 lg:grid-cols-[1.3fr_1fr]">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.05 }}
          className="panel p-5 md:p-6"
        >
          <h2 className="display-font text-3xl text-[#12203b] md:text-4xl">Strategy Builder</h2>
          <p className="mt-1 text-sm subtle">Tune race conditions and create up to six strategy variants.</p>

          <div className="mt-5 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <div>
              <label className="label">Season</label>
              <select className="input-base" value={year} onChange={(e) => setYear(Number(e.target.value))}>
                {years.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Race</label>
              <select className="input-base" value={round} onChange={(e) => setRound(Number(e.target.value))}>
                {races.map((raceOption) => (
                  <option key={raceOption.round} value={raceOption.round}>
                    {raceOption.round}. {raceOption.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Driver Model</label>
              <select className="input-base" value={driver} onChange={(e) => setDriver(e.target.value)}>
                <option value="">Field Median</option>
                {drivers.map((driverOption) => (
                  <option key={driverOption.code} value={driverOption.code}>
                    {driverOption.code} - {driverOption.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Pit Penalty ({pitPenalty.toFixed(1)}s)</label>
              <input
                type="range"
                min={14}
                max={32}
                step={0.5}
                value={pitPenalty}
                onChange={(e) => setPitPenalty(Number(e.target.value))}
                className="w-full"
              />
            </div>

            <div>
              <label className="label">Weather Risk ({Math.round(weatherRisk * 100)}%)</label>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={weatherRisk}
                onChange={(e) => setWeatherRisk(Number(e.target.value))}
                className="w-full"
              />
            </div>

            <div className="flex items-end gap-2">
              <button type="button" onClick={addStrategy} className="btn-secondary w-full" disabled={strategies.length >= 6}>
                Add Strategy
              </button>
            </div>
          </div>

          <div className="mt-5 space-y-3">
            {strategies.map((strategy, index) => (
              <div key={strategy.id} className="panel-muted p-3 md:p-4">
                <div className="grid gap-2 md:grid-cols-6">
                  <div className="md:col-span-2">
                    <label className="label">Name</label>
                    <input
                      className="input-base"
                      value={strategy.name}
                      onChange={(e) => updateStrategy(strategy.id, { name: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="label">Pit Laps</label>
                    <input
                      className="input-base"
                      value={strategy.pitLaps}
                      onChange={(e) => updateStrategy(strategy.id, { pitLaps: e.target.value })}
                      placeholder="18,39"
                    />
                  </div>

                  <div>
                    <label className="label">Start Tyre</label>
                    <select
                      className="input-base"
                      value={strategy.startCompound}
                      onChange={(e) =>
                        updateStrategy(strategy.id, {
                          startCompound: e.target.value as Compound,
                        })
                      }
                    >
                      <option value="SOFT">SOFT</option>
                      <option value="MEDIUM">MEDIUM</option>
                      <option value="HARD">HARD</option>
                    </select>
                  </div>

                  <div>
                    <label className="label">Tyre Profile</label>
                    <select
                      className="input-base"
                      value={strategy.tyreProfile}
                      onChange={(e) =>
                        updateStrategy(strategy.id, {
                          tyreProfile: e.target.value as TyreProfile,
                        })
                      }
                    >
                      <option value="aggressive">Aggressive</option>
                      <option value="balanced">Balanced</option>
                      <option value="conservative">Conservative</option>
                    </select>
                  </div>

                  <div>
                    <label className="label">Fuel Delta (s)</label>
                    <input
                      type="number"
                      min={-0.8}
                      max={1.5}
                      step={0.05}
                      className="input-base"
                      value={strategy.fuelSave}
                      onChange={(e) => updateStrategy(strategy.id, { fuelSave: Number(e.target.value) })}
                    />
                  </div>
                </div>

                <div className="mt-3 flex items-center justify-between">
                  <span
                    className="badge"
                    style={{ background: `${STRATEGY_COLORS[index % STRATEGY_COLORS.length]}22`, color: STRATEGY_COLORS[index % STRATEGY_COLORS.length] }}
                  >
                    Variant {index + 1}
                  </span>
                  <button
                    type="button"
                    onClick={() => removeStrategy(strategy.id)}
                    className="text-sm font-semibold text-[#8a1d31]"
                    disabled={strategies.length === 1}
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-5 flex flex-col gap-3 sm:flex-row">
            <button type="button" className="btn-primary flex-1" disabled={loading} onClick={handleRunAnalysis}>
              {loading ? "Running full analysis..." : "Run Strategy Intelligence"}
            </button>
            <button type="button" className="btn-secondary" onClick={handleCopyScenario}>
              {copied ? "Scenario Copied" : "Copy Shareable Scenario"}
            </button>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.12 }}
          className="panel p-5 md:p-6"
        >
          <h2 className="display-font text-3xl text-[#12203b] md:text-4xl">Race Intelligence</h2>
          <p className="mt-1 text-sm subtle">Key outputs from simulation and race context.</p>

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <div className="panel-muted p-4">
              <p className="text-xs uppercase tracking-[0.08em] subtle">Best Strategy</p>
              <p className="kpi-value mt-1 text-[#12203b]">{topStrategy?.name ?? "-"}</p>
              <p className="text-sm subtle">{topStrategy ? formatSeconds(topStrategy.total_time) : "Run analysis to compute ranking"}</p>
            </div>

            <div className="panel-muted p-4">
              <p className="text-xs uppercase tracking-[0.08em] subtle">Benchmark Source</p>
              <p className="kpi-value mt-1 text-[#12203b]">{simulation?.meta.baseline_source ?? "-"}</p>
              <p className="text-sm subtle">{simulation ? `${simulation.meta.total_laps} laps modeled` : "Awaiting simulation"}</p>
            </div>

            <div className="panel-muted p-4">
              <p className="text-xs uppercase tracking-[0.08em] subtle">Track Temperature</p>
              <p className="kpi-value mt-1 text-[#12203b]">{simulation ? `${simulation.race_context.weather.avg_track_temp.toFixed(1)}C` : "-"}</p>
              <p className="text-sm subtle">{simulation ? `Rain probability ${Math.round(simulation.race_context.weather.rain_probability * 100)}%` : "Weather profile appears after run"}</p>
            </div>

            <div className="panel-muted p-4">
              <p className="text-xs uppercase tracking-[0.08em] subtle">Safety Car Laps</p>
              <p className="kpi-value mt-1 text-[#12203b]">
                {simulation ? simulation.race_context.safety_car_laps.length : "-"}
              </p>
              <p className="text-sm subtle">
                {simulation?.race_context.safety_car_laps.length
                  ? simulation.race_context.safety_car_laps.slice(0, 5).join(", ")
                  : "No caution laps detected in dataset"}
              </p>
            </div>
          </div>

          <div className="panel-muted mt-4 p-4">
            <p className="text-xs uppercase tracking-[0.08em] subtle">Pit Window Radar</p>
            {!simulation?.pit_windows.length && <p className="mt-2 text-sm subtle">Run analysis to surface best undercut windows.</p>}
            {!!simulation?.pit_windows.length && (
              <ul className="mt-2 space-y-2">
                {simulation.pit_windows.map((window) => (
                  <li key={`${window.lap}-${window.label}`} className="flex items-center justify-between rounded-xl border border-[#d8d8cf] bg-white px-3 py-2 text-sm">
                    <span>
                      Lap {window.lap} <span className="subtle">({window.label})</span>
                    </span>
                    <span className="font-semibold text-[#0f66c3]">score {window.score.toFixed(3)}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </motion.div>
      </section>

      {error && (
        <div className="mt-6 rounded-2xl border border-[#efb8c2] bg-[#fff0f3] px-4 py-3 text-sm text-[#861c32]">{error}</div>
      )}

      {simulation && <SimulationResults simulation={simulation} />}

      <RaceInsights digest={digest} overtake={overtake} />
    </main>
  );
}
