import { Router } from "express";
import { config } from "../config";

const router = Router();

router.get("/runtime", async (_req, res, next) => {
  try {
    const upstream = await fetch(`${config.fastapiUrl}/intelligence/runtime`);
    const data = await upstream.json();
    res.status(upstream.status).json(data);
  } catch (err) {
    next(err);
  }
});

export default router;
