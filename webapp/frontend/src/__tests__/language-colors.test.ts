import { describe, it, expect } from "vitest";
import { languageColor, languageLabel } from "@/lib/language-colors";

describe("languageColor", () => {
  it("gives the targets and replay languages their own fixed colours", () => {
    const names = [
      "sinhala", "pali", "sanskrit", "English", "Tamil", "Hindi", "Bengali",
      "Arabic", "French", "German", "Sanskrit (Devanagari)",
    ];
    const marks = names.map((n) => languageColor(n).mark);
    expect(new Set(marks).size).toBe(names.length);
    expect(languageColor("sinhala").mark).toBe("bg-blue-100");
    expect(languageColor("pali").mark).toBe("bg-emerald-100");
    expect(languageColor("sanskrit").mark).toBe("bg-violet-100");
  });

  it("colours any other language from a stable hash, apart from the fixed ones", () => {
    const fixed = new Set(["sinhala", "pali", "English", "French"].map((n) => languageColor(n).mark));
    for (const other of ["Chinese", "Spanish", "Italian", "vi", "el", "Persian", "Japanese"]) {
      const color = languageColor(other);
      expect(color).toEqual(languageColor(other)); // stable
      expect(fixed.has(color.mark)).toBe(false);
    }
    expect(languageColor("ENGLISH")).toEqual(languageColor("English")); // case-insensitive
  });

  it("keeps unknown neutral", () => {
    expect(languageColor("unknown").mark).toBe("bg-slate-100");
    expect(languageColor("").mark).toBe("bg-slate-100");
  });
});

describe("languageLabel", () => {
  it("capitalises the targets and keeps names", () => {
    expect(languageLabel("pali")).toBe("Pali");
    expect(languageLabel("English")).toBe("English");
    expect(languageLabel("Sanskrit (Devanagari)")).toBe("Sanskrit (Devanagari)");
  });

  it("names bare language codes", () => {
    expect(languageLabel("vi")).toBe("Vietnamese");
    expect(languageLabel("el")).toBe("Greek");
    expect(languageLabel("ceb")).toBe("Cebuano");
    expect(languageLabel("san_Latn")).toBe("Sanskrit (Latin)");
  });
});
