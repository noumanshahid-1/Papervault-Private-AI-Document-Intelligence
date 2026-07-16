import type { DatedEntry } from "./types";

// =============================================================================
// Time-sensitivity detection
// =============================================================================
// Comprehensive pattern set that catches dates, times, time zones, durations,
// and deadline keywords in any plausible document. Order is intentional:
// HINT_PATTERNS are scanned for extractTimeHint() and contribute concrete date
// strings to important_dates. DEADLINE_KEYWORDS only flag urgency — they don't
// produce useful hints on their own. isTimeSensitive() returns true if either
// list matches.

const MONTH = "(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)";
const DAY_NAME = "(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Mon|Tue|Tues|Wed|Thu|Thur|Thurs|Fri|Sat|Sun)";
const YEAR4 = "(?:19|20)\\d{2}";
const ORDINAL = "(?:st|nd|rd|th)";

// Patterns that yield a useful concrete hint string when matched
// (e.g. "15 July 2025", "06.30 am", "within 14 days", "GMT+7").
const HINT_PATTERNS: { name: string; re: RegExp }[] = [
  // --- Full calendar dates (most specific first) ---
  { name: "date-iso", re: new RegExp(`\\b${YEAR4}-\\d{1,2}-\\d{1,2}\\b`) },                                        // 2025-07-15
  { name: "date-dmy-long", re: new RegExp(`\\b\\d{1,2}${ORDINAL}?\\s+${MONTH}\\s+${YEAR4}\\b`, "i") },             // 15 July 2025
  { name: "date-mdy-long", re: new RegExp(`\\b${MONTH}\\s+\\d{1,2}${ORDINAL}?,?\\s+${YEAR4}\\b`, "i") },           // July 15, 2025
  { name: "date-slash-full", re: /\b\d{1,2}[/.-]\d{1,2}[/.-](?:19|20)\d{2}\b/ },                              // 15/07/2025
  { name: "date-slash-short", re: /\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2}\b/ },                                      // 15/07/25
  { name: "date-month-year", re: new RegExp(`\\b${MONTH}\\s+${YEAR4}\\b`, "i") },                                 // July 2025
  { name: "date-dmy-short", re: new RegExp(`\\b\\d{1,2}${ORDINAL}?\\s+${MONTH}\\b`, "i") },                       // 15 July, 15th July
  { name: "date-mdy-short", re: new RegExp(`\\b${MONTH}\\s+\\d{1,2}${ORDINAL}?\\b`, "i") },                       // July 15, July 15th
  { name: "date-dayname-with", re: new RegExp(`\\b${DAY_NAME}\\s*,?\\s+${MONTH}\\s+\\d{1,2}${ORDINAL}?\\b`, "i") },// Monday, July 15
  { name: "date-dayname", re: new RegExp(`\\b${DAY_NAME}\\b`, "i") },                                              // Monday

  // --- Times ---
  { name: "time-hhmm-ampm", re: /\b\d{1,2}[:.]\d{2}\s*(?:am|pm|a\.m\.|p\.m\.)\b/i },                              // 06:30 am, 06.30 pm
  { name: "time-h-ampm", re: /\b\d{1,2}\s*(?:am|pm|a\.m\.|p\.m\.)\b/i },                                          // 6 am, 9PM
  { name: "time-24h", re: /\b(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?(?:\s*(?:hrs?|hours?))?\b/i },                // 14:30, 14:30 hrs
  { name: "time-keyword", re: /\b(?:noon|midnight|midday|tonight|this\s+morning|this\s+afternoon|this\s+evening)\b/i },
  { name: "time-window", re: /\b\d{1,2}\s*(?:am|pm)\s*(?:to|-|–|—)\s*\d{1,2}\s*(?:am|pm)\b/i },                  // 9am to 5pm

  // --- Time zones / offsets ---
  { name: "tz-named", re: /\b(?:GMT|UTC|EST|EDT|CST|CDT|MST|MDT|PST|PDT|BST|CET|CEST|EET|EEST|JST|KST|IST|PKT|WIB|WITA|WIT|AEST|AEDT|NZST|NZDT|HKT|SGT)\b(?:[+-]\d{1,2}(?::?\d{2})?)?/ },
  { name: "tz-offset", re: /\b(?:UTC|GMT)\s*[+-]\s*\d{1,2}(?::?\d{2})?\b/i },                                     // GMT+7, UTC-05:30

  // --- Relative & durative timing ---
  { name: "within-period", re: /\bwithin\s+(?:the\s+next\s+)?\d+\s*(?:business\s+|working\s+)?(?:days?|hours?|weeks?|months?|years?|minutes?|mins?|hrs?|seconds?|secs?)\b/i },
  { name: "in-period", re: /\bin\s+(?:the\s+next\s+)?\d+\s*(?:business\s+|working\s+)?(?:days?|hours?|weeks?|months?|years?|minutes?|mins?|hrs?)\b/i },
  { name: "n-before-event", re: /\b\d+\s*(?:business\s+|working\s+)?(?:days?|hours?|weeks?|months?|minutes?|mins?|hrs?)\s+(?:before|prior\s+to|ahead\s+of|in\s+advance\s+of)\b/i },
  { name: "n-after-event", re: /\b\d+\s*(?:business\s+|working\s+)?(?:days?|hours?|weeks?|months?|minutes?|mins?|hrs?)\s+(?:after|following|from|of\s+receipt)\b/i },
  { name: "n-from-now", re: /\b\d+\s*(?:days?|weeks?|months?|years?|hours?)\s+(?:from\s+(?:now|today|the\s+date|receipt|issue)|hence)\b/i },
  { name: "for-duration", re: /\bfor\s+(?:a\s+period\s+of\s+)?\d+\s*(?:days?|weeks?|months?|years?|hours?|minutes?)\b/i },
  { name: "every-period", re: /\bevery\s+(?:other\s+)?(?:day|week|month|year|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d+\s*(?:days?|weeks?|months?|years?))\b/i },
  { name: "weekday-relative", re: /\b(?:today|tomorrow|yesterday|this\s+(?:week|month|year|monday|tuesday|wednesday|thursday|friday|saturday|sunday)|next\s+(?:week|month|year|monday|tuesday|wednesday|thursday|friday|saturday|sunday)|last\s+(?:week|month|year))\b/i },
  { name: "end-of-period", re: /\b(?:by\s+)?(?:the\s+)?end\s+of\s+(?:this\s+|next\s+|the\s+)?(?:day|week|month|quarter|year|business\s+day)\b/i },
  { name: "by-cob", re: /\bby\s+(?:close\s+of\s+business|COB|EOD|end\s+of\s+day)\b/i },

  // --- Date-anchored deadline phrases (capture both keyword + date) ---
  { name: "by-date-long", re: new RegExp(`\\bby\\s+\\d{1,2}${ORDINAL}?\\s+${MONTH}(?:\\s+${YEAR4})?\\b`, "i") },        // by 15 July, by 15 July 2025
  { name: "by-date-month-day", re: new RegExp(`\\bby\\s+${MONTH}\\s+\\d{1,2}${ORDINAL}?(?:,?\\s+${YEAR4})?\\b`, "i") }, // by July 15
  { name: "before-date-long", re: new RegExp(`\\bbefore\\s+\\d{1,2}${ORDINAL}?\\s+${MONTH}(?:\\s+${YEAR4})?\\b`, "i") },
  { name: "before-date-mdy", re: new RegExp(`\\bbefore\\s+${MONTH}\\s+\\d{1,2}${ORDINAL}?(?:,?\\s+${YEAR4})?\\b`, "i") },
  { name: "on-date-long", re: new RegExp(`\\bon\\s+\\d{1,2}${ORDINAL}?\\s+${MONTH}(?:\\s+${YEAR4})?\\b`, "i") },
];

// Patterns that signal urgency but rarely include a useful hint by themselves.
const DEADLINE_KEYWORDS: RegExp[] = [
  /\bdeadlines?\b/i,
  /\bdue\s+date\b/i,
  /\bdue\s+(?:by|on|before|within)\b/i,
  /\bcut[\s-]?off\s+(?:date|time)?\b/i,
  /\blast\s+(?:date|day)\b/i,
  /\bexpir(?:y|es?|ation|ing)\b/i,
  /\bvalid\s+(?:until|through|till|up\s+to)\b/i,
  /\bbinding\s+(?:by|until)\b/i,
  /\b(?:must|shall|have\s+to|need\s+to)\s+(?:be|submit|provide|complete|confirm|pay|attend|register|respond|sign|return|file|present|appear|show)\b/i,
  /\bare\s+required\s+to\b/i,
  /\bis\s+required\s+to\b/i,
  /\bmandatory\b/i,
  /\bcompulsor(?:y|ily)\b/i,
  /\bnon[\s-]?negotiable\b/i,
  /\bobligator(?:y|ily)\b/i,
  /\b(?:ensure|please\s+ensure|kindly\s+ensure|make\s+sure)\b/i,
  /\b(?:immediately|urgently?|urgent|ASAP|right\s+away|without\s+delay|forthwith)\b/i,
  /\bas\s+soon\s+as\s+possible\b/i,
  /\bprior\s+to\b/i,
  /\bno\s+later\s+than\b/i,
  /\bnot\s+later\s+than\b/i,
  /\bon\s+or\s+before\b/i,
  /\bschedul(?:ed?|ing)\s+(?:at|for|on|to)\b/i,
  /\b(?:appointment|consultation|hearing|interview|examination|test|meeting|session|interview)\s+(?:on|at|scheduled|booked)\b/i,
  /\b(?:submit|complete|provide|pay|return|confirm|respond|reply|file|register|sign|deliver|hand\s+in)\s+(?:by|before|on|within|no\s+later\s+than)\b/i,
  /\b(?:arrive|be\s+present|report|check[\s-]?in|attend)\s+(?:\d+\s*(?:minutes?|mins?|hours?|hrs?)\s+(?:before|early|ahead|in\s+advance)|on\s+time|punctually|promptly)\b/i,
  /\bpenalt(?:y|ies)\s+for\s+(?:late|delay|missing)\b/i,
  /\blate\s+(?:submission|payment|filing|fee)\b/i,
  /\bgrace\s+period\b/i,
  /\beffective\s+(?:from|on|date)\b/i,
  /\bcommences?\s+on\b/i,
  /\bstarts?\s+on\b/i,
  /\bends?\s+on\b/i,
];

export function isTimeSensitive(text: string): boolean {
  return HINT_PATTERNS.some((p) => p.re.test(text))
      || DEADLINE_KEYWORDS.some((p) => p.test(text));
}

// Per-pattern score — concrete dates with year > times > durations > weekday.
// Higher = more informative. Used by extractTimeHint to pick the best match.
const PATTERN_SCORE: Record<string, number> = {
  // Hard dates anchored to deadline phrases
  "by-date-long": 120, "by-date-month-day": 120,
  "before-date-long": 120, "before-date-mdy": 120,
  "on-date-long": 110,
  // Full calendar dates
  "date-iso": 100, "date-dmy-long": 100, "date-mdy-long": 100,
  "date-slash-full": 95, "date-slash-short": 80,
  // Date-name with month: "Thursday, July 15"
  "date-dayname-with": 55,
  // Month + year
  "date-month-year": 70,
  // Day + month / month + day (no year)
  "date-dmy-short": 60, "date-mdy-short": 60,
  // Bare day-name — least specific
  "date-dayname": 10,
  // Times
  "time-hhmm-ampm": 75, "time-24h": 70, "time-h-ampm": 55,
  "time-keyword": 35, "time-window": 50,
  // Time zones
  "tz-named": 25, "tz-offset": 30,
  // Relative / duration
  "within-period": 55, "in-period": 55,
  "n-before-event": 55, "n-after-event": 55,
  "n-from-now": 55, "for-duration": 30,
  "every-period": 30, "weekday-relative": 20,
  "end-of-period": 35, "by-cob": 55,
};

export function extractTimeHint(text: string): string | null {
  let best: { hit: string; score: number } | null = null;
  for (const { name, re } of HINT_PATTERNS) {
    const m = text.match(re);
    if (!m || !m[0]) continue;
    // Base score by pattern type + a tiny length tiebreaker
    const score = (PATTERN_SCORE[name] ?? 5) + m[0].length * 0.1;
    if (!best || score > best.score) best = { hit: m[0], score };
  }
  return best?.hit ?? null;
}

// Pull every distinct hint from a body of text — used by mapInsight to surface
// dates/times the Python analyzer missed.
export function extractAllHints(text: string): string[] {
  const hits = new Set<string>();
  for (const { re } of HINT_PATTERNS) {
    const global = new RegExp(re.source, re.flags.includes("g") ? re.flags : re.flags + "g");
    let m: RegExpExecArray | null;
    while ((m = global.exec(text)) !== null) {
      const hit = m[0].trim();
      if (hit.length >= 2) hits.add(hit);
      if (m.index === global.lastIndex) global.lastIndex++;
    }
  }
  return Array.from(hits);
}

// =============================================================================
// Date parsing & dedup — collapse "21 May 2026" / "21st May 2026" / "21/05/2026"
// into a single canonical entry. Subsumes vague mentions (bare "21 May") when
// a more specific one (with year) is present. Drops bare day-name fragments.
// =============================================================================

const MONTH_NUM: Record<string, number> = {
  jan: 1, january: 1,
  feb: 2, february: 2,
  mar: 3, march: 3,
  apr: 4, april: 4,
  may: 5,
  jun: 6, june: 6,
  jul: 7, july: 7,
  aug: 8, august: 8,
  sep: 9, sept: 9, september: 9,
  oct: 10, october: 10,
  nov: 11, november: 11,
  dec: 12, december: 12,
};
const MONTH_NAMES_ALT = Object.keys(MONTH_NUM).join("|");
const DAY_NAMES_RX = /^(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)$/i;

interface ParsedDate {
  y: number | null;
  m: number | null;
  d: number | null;
  dayName: string | null;
  // Source pattern role — date / time / duration / keyword etc.
  kind: "date" | "time" | "duration" | "tz" | "weekday" | "other";
}

function normYear(y: number): number {
  return y < 100 ? 2000 + y : y;
}

function parseDateLoose(raw: string): ParsedDate | null {
  let s = raw.toLowerCase().replace(/(\d+)(st|nd|rd|th)\b/g, "$1").replace(/[,]/g, "").trim();
  if (!s) return null;
  s = s.replace(/^(?:by|before|on)\s+/, "");

  // Day-name only
  if (DAY_NAMES_RX.test(s)) {
    return { y: null, m: null, d: null, dayName: s.slice(0, 3), kind: "weekday" };
  }

  // Strip leading day-name prefix so "thursday 21 may 2026" parses as a date
  // (and the resulting kind is "date", not "weekday").
  const dayPrefix = s.match(/^(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)\s+/);
  if (dayPrefix) {
    s = s.slice(dayPrefix[0].length).trim();
    if (!s) return { y: null, m: null, d: null, dayName: dayPrefix[1].slice(0, 3), kind: "weekday" };
  }

  // ISO 2026-05-21
  let m = s.match(/^(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})$/);
  if (m) return { y: +m[1], m: +m[2], d: +m[3], dayName: null, kind: "date" };

  // DMY long: "21 may 2026"
  m = s.match(new RegExp(`^(\\d{1,2})\\s+(${MONTH_NAMES_ALT})\\s+(\\d{2,4})$`));
  if (m) return { y: normYear(+m[3]), m: MONTH_NUM[m[2]], d: +m[1], dayName: null, kind: "date" };

  // MDY long: "may 21 2026"
  m = s.match(new RegExp(`^(${MONTH_NAMES_ALT})\\s+(\\d{1,2})\\s+(\\d{2,4})$`));
  if (m) return { y: normYear(+m[3]), m: MONTH_NUM[m[1]], d: +m[2], dayName: null, kind: "date" };

  // Slash form — assume DMY (international docs)
  m = s.match(/^(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})$/);
  if (m) {
    const d = +m[1], mo = +m[2];
    // If "first" component > 12, must be day
    return { y: normYear(+m[3]), m: mo, d, dayName: null, kind: "date" };
  }

  // Month + year only: "may 2026"
  m = s.match(new RegExp(`^(${MONTH_NAMES_ALT})\\s+(\\d{4})$`));
  if (m) return { y: +m[2], m: MONTH_NUM[m[1]], d: null, dayName: null, kind: "date" };

  // Day + month only: "21 may"
  m = s.match(new RegExp(`^(\\d{1,2})\\s+(${MONTH_NAMES_ALT})$`));
  if (m) return { y: null, m: MONTH_NUM[m[2]], d: +m[1], dayName: null, kind: "date" };

  // Month + day only: "may 21"
  m = s.match(new RegExp(`^(${MONTH_NAMES_ALT})\\s+(\\d{1,2})$`));
  if (m) return { y: null, m: MONTH_NUM[m[1]], d: +m[2], dayName: null, kind: "date" };

  // Times: "06.30 am", "14:30"
  if (/^\d{1,2}[:.]\d{2}\s*(?:am|pm|a\.m\.|p\.m\.)?$/.test(s) ||
      /^\d{1,2}:\d{2}(?::\d{2})?$/.test(s) ||
      /^\d{1,2}\s*(?:am|pm|a\.m\.|p\.m\.)$/.test(s)) {
    return { y: null, m: null, d: null, dayName: null, kind: "time" };
  }

  // Durations: "15 minutes before", "within 14 days"
  if (/(?:minutes?|mins?|hours?|hrs?|days?|weeks?|months?|years?|seconds?|secs?)/.test(s)) {
    return { y: null, m: null, d: null, dayName: null, kind: "duration" };
  }

  // Time zone: GMT+7, WIB, PKT
  if (/^(?:gmt|utc|est|edt|cst|cdt|mst|mdt|pst|pdt|bst|cet|cest|wib|wita|wit|jst|kst|ist|pkt|aest|aedt|nzst|nzdt|hkt|sgt)(?:[+-]\d{1,2}(?::?\d{2})?)?$/i.test(s)) {
    return { y: null, m: null, d: null, dayName: null, kind: "tz" };
  }

  return { y: null, m: null, d: null, dayName: null, kind: "other" };
}

function dateSpecificity(p: ParsedDate): number {
  if (p.y && p.m && p.d) return 100;
  if (p.m && p.d) return 60;
  if (p.y && p.m) return 40;
  if (p.kind === "time") return 30;
  if (p.kind === "duration") return 20;
  if (p.kind === "tz") return 15;
  if (p.dayName) return 5;
  return 1;
}

function canonKey(p: ParsedDate, raw: string): string {
  if (p.kind === "date") return `d:${p.y ?? "*"}-${p.m ?? "*"}-${p.d ?? "*"}`;
  if (p.dayName) return `dn:${p.dayName}`;
  // For times/durations/tz/other use a normalized text key to dedup near-duplicates
  return `${p.kind}:${raw.toLowerCase().replace(/\s+/g, " ").trim()}`;
}

// Collapse a list of raw date/time strings into a deduplicated, ranked list.
// Drops bare day-names if any concrete date is present and drops vague dates
// (no year) that are subsumed by a fully-specified date with the same m+d.
export function dedupAndRankDates(raw: string[]): string[] {
  const parsed = raw
    .map((r) => ({ raw: r, p: parseDateLoose(r) }))
    .filter((e): e is { raw: string; p: ParsedDate } => e.p !== null);

  // Group by canonical key, keep longest raw form per group.
  const groups = new Map<string, { raw: string; p: ParsedDate; spec: number }>();
  for (const e of parsed) {
    const key = canonKey(e.p, e.raw);
    const spec = dateSpecificity(e.p);
    const existing = groups.get(key);
    if (!existing || e.raw.length > existing.raw.length) {
      groups.set(key, { raw: e.raw, p: e.p, spec });
    }
  }

  const all = Array.from(groups.values());
  const hasConcreteDate = all.some((e) => e.p.kind === "date" && e.p.m !== null);

  const kept = all.filter((e) => {
    // Drop bare day-names when any concrete date exists
    if (e.p.dayName && hasConcreteDate) return false;

    // Drop vague dates subsumed by a fully-specified one
    if (e.p.kind === "date" && e.spec < 100) {
      const subsumer = all.find((o) =>
        o !== e &&
        o.p.kind === "date" &&
        o.spec === 100 &&
        (e.p.y === null || o.p.y === e.p.y) &&
        (e.p.m === null || o.p.m === e.p.m) &&
        (e.p.d === null || o.p.d === e.p.d)
      );
      if (subsumer) return false;
    }
    return true;
  });

  // Sort: concrete dates by chronological order first, then times, durations,
  // tz, weekdays, others. Specificity desc within each kind.
  kept.sort((a, b) => {
    const kindOrder = { date: 0, time: 1, duration: 2, tz: 3, weekday: 4, other: 5 } as const;
    const ka = kindOrder[a.p.kind] ?? 9;
    const kb = kindOrder[b.p.kind] ?? 9;
    if (ka !== kb) return ka - kb;
    if (a.p.kind === "date") {
      const ay = a.p.y ?? 9999, by = b.p.y ?? 9999;
      if (ay !== by) return ay - by;
      const am = a.p.m ?? 99, bm = b.p.m ?? 99;
      if (am !== bm) return am - bm;
      const ad = a.p.d ?? 99, bd = b.p.d ?? 99;
      return ad - bd;
    }
    return b.spec - a.spec;
  });

  return kept.map((e) => e.raw);
}

// =============================================================================
// Sentence-level deadline detection — distinguishes hard deadlines from
// incidental date mentions.
// =============================================================================

export function splitSentences(text: string): string[] {
  return text
    .split(/(?<=[.!?])\s+|\n+/)
    .map((s) => s.replace(/\s+/g, " ").trim())
    .filter((s) => s.length > 6 && s.length < 320);
}

// A sentence carries a deadline if it has BOTH a concrete date/time hint AND
// a deadline keyword — or if a nearby sentence in the same passage carries
// the deadline keyword. Academic docs commonly split these across sentences
// (e.g. "Presentations on 21 May." then "Each group must arrive on time.").
const NEIGHBOR_WINDOW = 2; // sentences before/after to consider for deadline-keyword proximity

function sentenceHasDeadlineKw(sentence: string): boolean {
  return DEADLINE_KEYWORDS.some((p) => p.test(sentence));
}

export function buildKeyDeadlines(text: string): DatedEntry[] {
  if (!text) return [];
  const sentences = splitSentences(text);
  const entries: DatedEntry[] = [];
  const seenContexts = new Set<string>();

  for (let i = 0; i < sentences.length; i++) {
    const s = sentences[i];
    const hint = extractTimeHint(s);
    if (!hint) continue;

    // The hint must be a real date/time/duration — skip bare day-name fragments.
    const parsed = parseDateLoose(hint);
    if (!parsed || parsed.kind === "weekday" || parsed.kind === "other") continue;

    const start = Math.max(0, i - NEIGHBOR_WINDOW);
    const end = Math.min(sentences.length, i + NEIGHBOR_WINDOW + 1);
    let hasUrgency = false;
    for (let j = start; j < end; j++) {
      if (sentenceHasDeadlineKw(sentences[j])) { hasUrgency = true; break; }
    }
    if (!hasUrgency) continue;

    const ctxKey = s.toLowerCase().replace(/\s+/g, " ");
    if (seenContexts.has(ctxKey)) continue;
    seenContexts.add(ctxKey);

    entries.push({
      text: hint,
      context: s,
      is_deadline: true,
    });
  }

  // Dedup by hint canonical key (so "21 May 2026" deadline appears once even
  // if mentioned in multiple sentences — keep the first context).
  const byCanon = new Map<string, DatedEntry>();
  for (const e of entries) {
    const p = parseDateLoose(e.text);
    const key = p ? canonKey(p, e.text) : `t:${e.text.toLowerCase()}`;
    if (!byCanon.has(key)) byCanon.set(key, e);
  }
  return Array.from(byCanon.values());
}

// =============================================================================
// Priority transparency — return human-readable reasons a sentence was
// flagged as time-sensitive / high-priority.
// =============================================================================

function categoryLabel(name: string): string {
  if (name.startsWith("date-")) return "Date";
  if (name.startsWith("time-")) return "Time";
  if (name.startsWith("tz-")) return "Time zone";
  if (name.startsWith("within-") || name.startsWith("in-period") || name.startsWith("n-") || name.startsWith("for-") || name.startsWith("every-") || name.startsWith("end-of-") || name.startsWith("by-cob") || name.startsWith("weekday-relative")) return "Duration";
  if (name.startsWith("by-") || name.startsWith("before-") || name.startsWith("on-date")) return "Deadline phrase";
  return "Time reference";
}

export function explainPriority(text: string): string[] {
  const reasons: string[] = [];
  const seen = new Set<string>();

  for (const { name, re } of HINT_PATTERNS) {
    const m = text.match(re);
    if (!m) continue;
    const label = `${categoryLabel(name)}: "${m[0]}"`;
    if (!seen.has(label)) { seen.add(label); reasons.push(label); }
  }
  for (const re of DEADLINE_KEYWORDS) {
    const m = text.match(re);
    if (!m) continue;
    const label = `Urgency phrase: "${m[0]}"`;
    if (!seen.has(label)) { seen.add(label); reasons.push(label); }
  }
  // Cap to avoid overwhelming the panel
  return reasons.slice(0, 5);
}

// =============================================================================
// List cleanup — strip PDF artifacts, dedup, split paragraph dumps.
// =============================================================================

// Normalize all common PDF/Word bullet glyphs to a single sentinel " ¶ ", so
// we can dedup, clean, and split on one consistent marker downstream.
// Covers: geometric shapes (U+25A0–U+25FF), dingbats/arrows (U+27xx), Private
// Use Area glyphs that PDF extractors sometimes emit (U+F000–U+F8FF), and the
// most common stray markers (•, ‣, ⁃, ◦, ∙, ▪, ▫). Also catches the lone
// lowercase " o " marker that PyMuPDF emits in numbered lists.
const PDF_BULLETS_RX = /[■-◿☀-⛿✀-➿•‣◦⁃∙-]+/g;
const LOWERCASE_O_BULLET_RX = /\s+o\s+/g;
const SENTINEL = " ¶ ";

function cleanLine(s: string): string {
  return s
    .replace(PDF_BULLETS_RX, SENTINEL)
    .replace(LOWERCASE_O_BULLET_RX, SENTINEL)
    .replace(/\s+/g, " ")
    .trim()
    // Strip a leading/trailing sentinel that has nothing useful next to it.
    .replace(/^¶\s*|\s*¶$/g, "")
    .trim();
}

// Split on the normalized sentinel — runs after cleanLine. Single-item lists
// (no sentinel inside) pass through unchanged.
function splitParagraphDump(s: string): string[] {
  if (!s.includes("¶")) return [s];
  return s
    .split(/\s*¶\s*/)
    .map((p) => p.replace(/\s+/g, " ").trim())
    .filter((p) => p.length >= 3);
}

export function cleanList(items: string[]): string[] {
  const out: string[] = [];
  const seen = new Set<string>();
  for (const raw of items) {
    const cleaned = cleanLine(raw);
    if (!cleaned) continue;
    for (const part of splitParagraphDump(cleaned)) {
      const key = part.toLowerCase().replace(/\s+/g, " ");
      if (seen.has(key)) continue;
      seen.add(key);
      out.push(part);
    }
  }
  return out;
}

// Heuristic: keep entries that look like real contact info (email / phone /
// URL / postal address). Drops noise like year ranges or doc numbers.
const EMAIL_RX = /\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b/;
const URL_RX = /\bhttps?:\/\/\S+\b/i;
const PHONE_RX = /(?:\+?\d[\d\s().-]{6,}\d)/;
const ADDRESS_KW_RX = /\b(?:street|road|avenue|lane|drive|st\.|rd\.|ave\.|blvd|sector|colony|district|tehsil|po\s*box|postal\s*code|zip|zip\s*code|building|floor)\b/i;
const PURE_YEAR_RANGE_RX = /^\d{4}\s*[-–—]\s*\d{4}$/;

export function isLikelyContact(s: string): boolean {
  const t = s.trim();
  if (!t || PURE_YEAR_RANGE_RX.test(t)) return false;
  if (EMAIL_RX.test(t)) return true;
  if (URL_RX.test(t)) return true;
  if (ADDRESS_KW_RX.test(t)) return true;
  // Phone: needs 7+ digits not part of a year range
  const phoneM = t.match(PHONE_RX);
  if (phoneM) {
    const digits = phoneM[0].replace(/\D/g, "");
    if (digits.length >= 7) return true;
  }
  return false;
}
