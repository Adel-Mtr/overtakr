import axios from "axios";

export type Compound = "SOFT" | "MEDIUM" | "HARD";
export type TyreProfile = "aggressive" | "balanced" | "conservative";

export type RaceOption = {
  round: number;
  name: string;
  country?: string | null;
  location?: string | null;
  date?: string | null;
};

export type DriverOption = {
  code: string;
  name: string;
  team: string;
  number: number;
  position: number;
};

export type StrategyPayload = {
  name: string;
  pit_laps: string;
  start_compound: Compound;
  tyre_profile: TyreProfile;
  fuel_save: number;
};

export type SimLap = {
  lap: number;
  lap_time: number;
  cumulative: number;
  compound: Compound;
  pit: boolean;
  safety_car: boolean;
  degradation: number;
};

export type SimStint = {
  compound: Compound;
  start_lap: number;
  end_lap: number;
  laps: number;
};

export type SimStrategyResult = {
  total_time: number;
  average_lap: number;
  pits: number;
  stints: SimStint[];
  laps: SimLap[];
};

export type SimulationResponse = {
  meta: {
    race: string;
    year: number;
    round: number;
    total_laps: number;
    baseline_source: string;
    generated_at: string;
  };
  race_context: {
    weather: {
      avg_air_temp: number;
      avg_track_temp: number;
      rain_probability: number;
      wind_speed_avg: number;
    };
    safety_car_laps: number[];
    pit_penalty: number;
    weather_risk: number;
  };
  strategies: Record<string, SimStrategyResult>;
  leaderboard: Array<{
    name: string;
    total_time: number;
    gap_to_best: number;
    pits: number;
    avg_lap: number;
  }>;
  pit_windows: Array<{
    lap: number;
    score: number;
    label: string;
  }>;
};

export type DriverDigest = {
  driver: string;
  full_name: string;
  team: string;
  grid_position: number;
  finish_position: number;
  places_gained: number;
  best_lap: {
    lap: number;
    time: number;
  } | null;
  average_lap: number;
  consistency_std: number;
  stints: Array<{
    compound: string;
    start_lap: number;
    end_lap: number;
    laps: number;
  }>;
  storyline: string;
};

export type DriverDigestResponse = {
  year: number;
  round: number;
  race: string;
  digest: DriverDigest;
};

export type OvertakeEvent = {
  lap: number;
  driver: string;
  from: number;
  to: number;
  gain: number;
};

export type OvertakeMapResponse = {
  year: number;
  round: number;
  race: string;
  selected_driver?: string | null;
  lap_events: OvertakeEvent[];
  driver_swings: Array<{
    driver: string;
    grid: number;
    finish: number;
    net: number;
  }>;
  summary: {
    total_position_changes: number;
    most_active_lap: number | null;
  };
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
});

export async function fetchYears(): Promise<number[]> {
  const { data } = await api.get<{ years: number[] }>("/api/years");
  return data.years;
}

export async function fetchRaces(year: number): Promise<RaceOption[]> {
  const { data } = await api.get<{ year: number; races: RaceOption[] }>("/api/races", {
    params: { year },
  });
  return data.races;
}

export async function fetchDrivers(year: number, round: number): Promise<DriverOption[]> {
  const { data } = await api.get<{ year: number; round: number; drivers: DriverOption[] }>(
    "/api/drivers",
    { params: { year, round } }
  );
  return data.drivers;
}

export async function runSimulation(payload: {
  year: number;
  round: number;
  driver?: string;
  pit_penalty: number;
  weather_risk: number;
  strategies: StrategyPayload[];
}): Promise<SimulationResponse> {
  const { data } = await api.post<SimulationResponse>("/api/simulate", payload);
  return data;
}

export async function fetchDriverDigest(
  year: number,
  round: number,
  driver?: string
): Promise<DriverDigestResponse> {
  const { data } = await api.get<DriverDigestResponse>("/api/driver-digest", {
    params: {
      year,
      round,
      ...(driver ? { driver } : {}),
    },
  });
  return data;
}

export async function fetchOvertakeMap(
  year: number,
  round: number,
  driver?: string
): Promise<OvertakeMapResponse> {
  const { data } = await api.get<OvertakeMapResponse>("/api/overtake-map", {
    params: {
      year,
      round,
      ...(driver ? { driver } : {}),
    },
  });
  return data;
}
