import { Router } from "express";
import { config } from "../config";

const router = Router();

router.get("/", async (_req, res, next) => {
  try {
    const upstream = await fetch(`${config.fastapiUrl}/sessions`);
    const data = await upstream.json();
    res.status(upstream.status).json(data);
  } catch (err) {
    next(err);
  }
});

router.delete("/", async (_req, res, next) => {
  try {
    const upstream = await fetch(`${config.fastapiUrl}/sessions`, { method: "DELETE" });
    const data = await upstream.json();
    res.status(upstream.status).json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/:id", async (req, res, next) => {
  try {
    const upstream = await fetch(`${config.fastapiUrl}/sessions/${encodeURIComponent(req.params.id)}`);
    const data = await upstream.json();
    res.status(upstream.status).json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/", async (req, res, next) => {
  try {
    const upstream = await fetch(`${config.fastapiUrl}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req.body),
    });
    const data = await upstream.json();
    res.status(upstream.status).json(data);
  } catch (err) {
    next(err);
  }
});

export default router;
