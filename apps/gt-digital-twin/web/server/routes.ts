import type { Express } from "express";
import type { Server } from 'node:http';

// The dashboard ships static precomputed JSONs and an SPA — no /api endpoints
// are registered in v1. This file is kept as the place to add future routes
// (e.g., a live-recompute endpoint when run_forward becomes callable).
export async function registerRoutes(
  _httpServer: Server,
  _app: Express
): Promise<Server> {
  return _httpServer;
}
