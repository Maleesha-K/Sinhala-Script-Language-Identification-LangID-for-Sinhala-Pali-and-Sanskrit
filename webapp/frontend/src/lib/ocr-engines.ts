export type OCREngine = {
  id: string;
  label: string;
  description: string;
  is_default: boolean;
};

/** Display name for an engine id, falling back to the raw id. */
export function ocrEngineLabel(engines: OCREngine[], id: string | null | undefined): string {
  if (!id) return "—";
  return engines.find((e) => e.id === id)?.label ?? id;
}
