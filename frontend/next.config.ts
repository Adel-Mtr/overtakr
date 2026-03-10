import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    // Keep workspace root explicit when multiple lockfiles exist on the machine.
    root: process.cwd(),
  },
};

export default nextConfig;
