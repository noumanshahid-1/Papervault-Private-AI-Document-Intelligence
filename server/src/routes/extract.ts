import { Router } from "express";
import multer from "multer";
import { config } from "../config";

const router = Router();
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 25 * 1024 * 1024 } });

router.post("/", upload.single("file"), async (req, res, next) => {
  try {
    if (!req.file) {
      res.status(400).json({ detail: "No file provided." });
      return;
    }

    // Use native FormData + Blob — the npm `form-data` package returns a
    // Node stream that the global fetch() does not handle, causing FastAPI
    // to see a malformed multipart body.
    const form = new FormData();
    const blob = new Blob([new Uint8Array(req.file.buffer)], {
      type: req.file.mimetype || "application/octet-stream",
    });
    form.append("file", blob, req.file.originalname);

    const upstream = await fetch(`${config.fastapiUrl}/documents/extract`, {
      method: "POST",
      body: form,
    });

    const data = await upstream.json();
    res.status(upstream.status).json(data);
  } catch (err) {
    next(err);
  }
});

export default router;
