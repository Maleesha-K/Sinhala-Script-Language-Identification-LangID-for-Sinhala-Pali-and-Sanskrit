import { describe, it, expect } from "vitest";
import { layoutSegments, type Segment } from "@/components/classification/segments";

/** Segments as the backend's "sentence" strategy cuts them (classification_tasks.split_segments). */
function sentenceSegments(text: string, languages: string[]): Segment[] {
  const out: Segment[] = [];
  for (const m of text.matchAll(/[^.!?।\n]+(?:[.!?।\n]+|$)/g)) {
    if (!m[0].trim()) continue;
    const start = Array.from(text.slice(0, m.index)).length;
    out.push({
      id: `s${out.length}`,
      segment_index: out.length,
      text: m[0],
      predicted_language: languages[out.length] ?? languages[languages.length - 1],
      confidence: 0.9,
      start_char_offset: start,
      end_char_offset: start + Array.from(m[0]).length,
    });
  }
  return out;
}

const joined = (pieces: { text: string }[]) => pieces.map((p) => p.text).join("");

describe("layoutSegments", () => {
  const text =
    "එය උත්සාහ කර බැලීමට\n\nYou can access texts. Download them.\nSri Lanka Government Documents\n.\n\nOnline Typing Tools";

  it("reproduces the original text exactly, blank lines included", () => {
    const pieces = layoutSegments(text, sentenceSegments(text, ["sinhala", "English"]))!;
    expect(joined(pieces)).toBe(text);
  });

  it("highlights sentences without their trailing line breaks", () => {
    const pieces = layoutSegments(text, sentenceSegments(text, ["sinhala", "English"]))!;
    const highlighted = pieces.filter((p) => p.kind === "segment").map((p) => p.text);
    expect(highlighted).toEqual([
      "එය උත්සාහ කර බැලීමට",
      "You can access texts.",
      "Download them.",
      // The backend's terminator run [.!?।\n]+ takes the "." line with it;
      // the highlight keeps the line break inside, so the layout is unchanged.
      "Sri Lanka Government Documents\n.",
      "Online Typing Tools",
    ]);
    // No empty or whitespace-only highlight (the old empty boxes).
    expect(highlighted.every((t) => t.trim() === t && t.length > 0)).toBe(true);
  });

  it("joins same-language sentences on one line, but never across a line break", () => {
    const pieces = layoutSegments(text, sentenceSegments(text, ["sinhala", "English"]))!;
    const gap = pieces.find((p) => p.kind === "text" && p.text === " ")!;
    expect(gap).toMatchObject({ language: "English" });
    const lineBreaks = pieces.filter((p) => p.kind === "text" && p.text.includes("\n"));
    expect(lineBreaks.every((p) => p.kind === "text" && p.language === undefined)).toBe(true);
  });

  it("does not join sentences of different languages", () => {
    const mixed = "මනොපුබ්බඞ්ගමා ධම්මා. ශ්‍රී ලංකාව ලස්සනයි.";
    const pieces = layoutSegments(mixed, sentenceSegments(mixed, ["pali", "sinhala"]))!;
    const gap = pieces.find((p) => p.kind === "text")!;
    expect(gap).toMatchObject({ text: " " });
    expect(gap).not.toHaveProperty("language");
  });

  it("shows the unclassified rest as pending while the job runs", () => {
    const all = sentenceSegments(text, ["sinhala", "English"]);
    const running = layoutSegments(text, all.slice(0, 2), true)!;
    expect(joined(running)).toBe(text);
    const rest = running[running.length - 1];
    expect(rest).toMatchObject({ kind: "text", pending: true });
    expect(rest.text.startsWith(" Download them.")).toBe(true);

    const finished = layoutSegments(text, all.slice(0, 2), false)!;
    expect(finished[finished.length - 1]).toMatchObject({ pending: false });
  });

  it("counts offsets in code points, as Python does", () => {
    const withEmoji = "😀 Hello there.\nශ්‍රී ලංකාව.";
    const segments = sentenceSegments(withEmoji, ["English", "sinhala"]);
    expect(segments[0].start_char_offset).toBe(0);
    expect(segments[1].start_char_offset).toBe(Array.from("😀 Hello there.\n").length);
    expect(joined(layoutSegments(withEmoji, segments)!)).toBe(withEmoji);
  });

  it("returns null when the offsets do not belong to the text", () => {
    const segments = sentenceSegments(text, ["sinhala"]);
    expect(layoutSegments("different text", segments)).toBeNull();
  });
});
