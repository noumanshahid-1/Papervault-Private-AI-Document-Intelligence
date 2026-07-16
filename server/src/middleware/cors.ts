import cors from "cors";
import { config } from "../config";

export const corsMiddleware = cors({
  origin: config.nodeEnv === "production" ? false : config.corsOrigin,
  methods: ["GET", "POST", "OPTIONS"],
  allowedHeaders: ["Content-Type", "Accept"],
});
