import { NextFunction, Request, Response } from "express";

export function errorHandler(
  err: Error,
  _req: Request,
  res: Response,
  _next: NextFunction
): void {
  console.error("[BFF Error]", err.message);
  res.status(500).json({ detail: err.message ?? "Internal server error" });
}
