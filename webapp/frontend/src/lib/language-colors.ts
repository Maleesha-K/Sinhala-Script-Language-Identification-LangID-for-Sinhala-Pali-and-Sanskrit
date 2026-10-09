/**
 * Colours for classified languages.
 *
 * The three targets and the eight replay languages the fine-tuned models were
 * rehearsed on have fixed colours; any other language a model detects gets one
 * of the remaining colours from a hash of its name, so a language looks the
 * same in every view and every session.
 *
 * Class names are written out in full so Tailwind generates them.
 */

export type LanguageColor = {
  /** Highlight behind classified text. */
  mark: string;
  /** Chip / badge: background, border and text. */
  chip: string;
  /** Solid swatch: legend dots and distribution bars. */
  swatch: string;
  /** Text colour on the highlight. */
  text: string;
};

const PALETTE: Record<string, LanguageColor> = {
  blue:    { mark: "bg-blue-100",    chip: "bg-blue-50 border-blue-300 text-blue-800",          swatch: "bg-blue-500",    text: "text-blue-900" },
  emerald: { mark: "bg-emerald-100", chip: "bg-emerald-50 border-emerald-300 text-emerald-800", swatch: "bg-emerald-500", text: "text-emerald-900" },
  violet:  { mark: "bg-violet-100",  chip: "bg-violet-50 border-violet-300 text-violet-800",    swatch: "bg-violet-500",  text: "text-violet-900" },
  amber:   { mark: "bg-amber-100",   chip: "bg-amber-50 border-amber-300 text-amber-800",       swatch: "bg-amber-500",   text: "text-amber-900" },
  rose:    { mark: "bg-rose-100",    chip: "bg-rose-50 border-rose-300 text-rose-800",          swatch: "bg-rose-500",    text: "text-rose-900" },
  orange:  { mark: "bg-orange-100",  chip: "bg-orange-50 border-orange-300 text-orange-800",    swatch: "bg-orange-500",  text: "text-orange-900" },
  teal:    { mark: "bg-teal-100",    chip: "bg-teal-50 border-teal-300 text-teal-800",          swatch: "bg-teal-500",    text: "text-teal-900" },
  lime:    { mark: "bg-lime-100",    chip: "bg-lime-50 border-lime-400 text-lime-800",          swatch: "bg-lime-500",    text: "text-lime-900" },
  sky:     { mark: "bg-sky-100",     chip: "bg-sky-50 border-sky-300 text-sky-800",             swatch: "bg-sky-500",     text: "text-sky-900" },
  fuchsia: { mark: "bg-fuchsia-100", chip: "bg-fuchsia-50 border-fuchsia-300 text-fuchsia-800", swatch: "bg-fuchsia-500", text: "text-fuchsia-900" },
  indigo:  { mark: "bg-indigo-100",  chip: "bg-indigo-50 border-indigo-300 text-indigo-800",    swatch: "bg-indigo-500",  text: "text-indigo-900" },
  cyan:    { mark: "bg-cyan-100",    chip: "bg-cyan-50 border-cyan-300 text-cyan-800",          swatch: "bg-cyan-500",    text: "text-cyan-900" },
  pink:    { mark: "bg-pink-100",    chip: "bg-pink-50 border-pink-300 text-pink-800",          swatch: "bg-pink-500",    text: "text-pink-900" },
  yellow:  { mark: "bg-yellow-100",  chip: "bg-yellow-50 border-yellow-400 text-yellow-800",    swatch: "bg-yellow-500",  text: "text-yellow-900" },
  red:     { mark: "bg-red-100",     chip: "bg-red-50 border-red-300 text-red-800",             swatch: "bg-red-500",     text: "text-red-900" },
  green:   { mark: "bg-green-100",   chip: "bg-green-50 border-green-300 text-green-800",       swatch: "bg-green-500",   text: "text-green-900" },
  purple:  { mark: "bg-purple-100",  chip: "bg-purple-50 border-purple-300 text-purple-800",    swatch: "bg-purple-500",  text: "text-purple-900" },
  stone:   { mark: "bg-stone-200",   chip: "bg-stone-50 border-stone-300 text-stone-800",       swatch: "bg-stone-500",   text: "text-stone-900" },
};

// Languages the fine-tuned models know as targets or replay languages
// (backend app/ml/registry.py), keyed by the name segments carry.
const FIXED: Record<string, keyof typeof PALETTE> = {
  sinhala: "blue",
  pali: "emerald",
  sanskrit: "violet",
  english: "amber",
  tamil: "rose",
  hindi: "orange",
  bengali: "teal",
  arabic: "lime",
  french: "sky",
  german: "fuchsia",
  // Cyan, not a violet shade, so it stands apart from Sinhala-script Sanskrit.
  "sanskrit (devanagari)": "cyan",
};

// Colours not taken by FIXED, for every other language.
const EXTRA: (keyof typeof PALETTE)[] = ["indigo", "pink", "yellow", "red", "green", "purple", "stone"];

const UNKNOWN: LanguageColor = {
  mark: "bg-slate-100", chip: "bg-slate-50 border-slate-300 text-slate-600", swatch: "bg-slate-400", text: "text-slate-600",
};

/** FNV-1a: a stable, well-spread hash of a language name. */
function hash(name: string): number {
  let h = 2166136261;
  for (const ch of name) {
    h ^= ch.codePointAt(0)!;
    h = Math.imul(h, 16777619) >>> 0;
  }
  return h;
}

export function languageColor(language: string): LanguageColor {
  const key = language.trim().toLowerCase();
  if (!key || key === "unknown") return UNKNOWN;
  const fixed = FIXED[key];
  return PALETTE[fixed ?? EXTRA[hash(key) % EXTRA.length]];
}

// A bare ISO code ("vi", "ceb", "san_Latn"), which models emit for languages
// the backend has no name for.
const LANGUAGE_CODE = /^([a-z]{2,3})(?:_([A-Z][a-z]{3}))?$/;

function displayName(type: "language" | "script", code: string): string | null {
  try {
    const name = new Intl.DisplayNames(["en"], { type }).of(code);
    return name && name !== code ? name : null;
  } catch {
    return null;
  }
}

/**
 * Display name: segments store targets in lower case ("pali"), other
 * languages by name ("English") or, when unnamed, by code ("vi" → "Vietnamese").
 */
export function languageLabel(language: string): string {
  const code = LANGUAGE_CODE.exec(language);
  if (code) {
    const name = displayName("language", code[1]);
    if (name) {
      const script = code[2] && displayName("script", code[2]);
      return script ? `${name} (${script})` : name;
    }
  }
  return language ? language[0].toUpperCase() + language.slice(1) : language;
}
