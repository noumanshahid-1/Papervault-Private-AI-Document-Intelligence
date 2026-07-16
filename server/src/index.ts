import express from "express";
import { config } from "./config";
import { corsMiddleware } from "./middleware/cors";
import { errorHandler } from "./middleware/errorHandler";
import { requestLogger } from "./middleware/requestLogger";
import healthRouter from "./routes/health";
import extractRouter from "./routes/extract";
import analyzeRouter from "./routes/analyze";
import checklistRouter from "./routes/checklist";
import askRouter from "./routes/ask";
import sessionsRouter from "./routes/sessions";
import intelligenceRouter from "./routes/intelligence";
import path from "path";

const app = express();

app.use(corsMiddleware);
app.use(express.json());
app.use(requestLogger);

app.use("/api/health", healthRouter);
app.use("/api/extract", extractRouter);
app.use("/api/analyze", analyzeRouter);
app.use("/api/checklist", checklistRouter);
app.use("/api/ask", askRouter);
app.use("/api/sessions", sessionsRouter);
app.use("/api/intelligence", intelligenceRouter);

// Serve React build in production
if (config.nodeEnv === "production") {
  const staticDir = path.resolve(__dirname, "../../frontend/dist");
  app.use(express.static(staticDir));
  app.get("*", (_req, res) => {
    res.sendFile(path.join(staticDir, "index.html"));
  });
}

app.use(errorHandler);

app.listen(config.port, () => {
  console.log(`[BFF] Papervault server running on http://localhost:${config.port}`);
  console.log(`[BFF] Proxying to FastAPI at ${config.fastapiUrl}`);
});
