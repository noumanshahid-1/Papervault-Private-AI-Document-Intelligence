import { describe, expect, it } from "vitest";
import {
  buildKeyDeadlines,
  dedupAndRankDates,
  extractTimeHint,
} from "./documentSignals";

describe("document signals", () => {
  it("deduplicates equivalent dates and removes vague duplicates", () => {
    expect(
      dedupAndRankDates([
        "15 July 2026",
        "15th July 2026",
        "15 July",
        "Monday",
      ]),
    ).toEqual(["15th July 2026"]);
  });

  it("detects deadline context around a concrete date", () => {
    const deadlines = buildKeyDeadlines(
      "Applications close on 15 July 2026. You must submit the form before the deadline.",
    );

    expect(deadlines).toHaveLength(1);
    expect(deadlines[0]).toMatchObject({
      text: "on 15 July 2026",
      is_deadline: true,
    });
  });

  it("prefers concrete date hints over generic urgency words", () => {
    expect(extractTimeHint("You must respond by 15 July 2026.")).toBe(
      "by 15 July 2026",
    );
  });
});
