import { Router } from "express";
import { config } from "../config";

const router = Router();

router.get("/", async (_req, res, next) => {
  try {
    const upstream = await fetch(`${config.fastapiUrl}/health`);
    const data = await upstream.json();
    res.json(data);
  } catch (err) {
    next(err);
  }
});

export default router;
