import { Router } from "express";
import { config } from "../config";

const router = Router();

router.post("/", async (req, res, next) => {
  try {
    const upstream = await fetch(`${config.fastapiUrl}/documents/checklist`, {
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
