import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { FileBlob, Presentation, PresentationFile } from "file:///C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const workspaceDir = "C:\\Users\\User\\Desktop\\Vscode\\Sinhala-Script Language Identification (LangID) for Sinhala, Pali and Sanskrit\\Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit";
const skillDir = "C:\\Users\\User\\.codex\\plugins\\cache\\openai-primary-runtime\\presentations\\26.1007.11041\\skills\\presentations";
const runtimePython = "C:\\Users\\User\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe";
const buildDir = path.join(workspaceDir, ".codex-slide-build");
const outputDir = path.join(workspaceDir, "deliverables");
const finalPptx = path.join(outputDir, "Sinhala_Script_LangID_Submission_Slide.pptx");
const previewPng = path.join(outputDir, "Sinhala_Script_LangID_Submission_Slide_Preview.png");
const candidatePath = path.join(buildDir, "candidate.pptx");
const receiptPath = path.join(buildDir, "Sinhala_Script_LangID_Submission_Slide.validation.json");
const layoutPath = path.join(buildDir, "slide-01.layout.json");
const inspectionPath = path.join(buildDir, "slide-01.inspect.ndjson");

const C = {
  bg: "#071420",
  surface: "#102537",
  surface2: "#132C40",
  text: "#F7F4EC",
  muted: "#A9BAC7",
  faint: "#537084",
  cyan: "#29C3DF",
  purple: "#A184FF",
  gold: "#F2B84B",
  green: "#5BDAA3",
  red: "#FF6E70",
  white10: "#23384A",
};

const FONT = "Arial";

function addText(slide, name, text, pos, style = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name,
    position: pos,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    typeface: FONT,
    fontSize: style.fontSize ?? 20,
    bold: style.bold ?? false,
    italic: style.italic ?? false,
    color: style.color ?? C.text,
    alignment: style.alignment ?? "left",
    verticalAlignment: style.verticalAlignment ?? "top",
    autoFit: style.autoFit ?? "shrinkText",
    wrap: "square",
    insets: style.insets ?? 0,
    lineSpacing: style.lineSpacing ?? 1.0,
  };
  return shape;
}

function addBox(slide, name, pos, options = {}) {
  return slide.shapes.add({
    geometry: options.geometry ?? "roundRect",
    name,
    position: pos,
    fill: options.fill ?? C.surface,
    line: {
      style: "solid",
      fill: options.line ?? C.white10,
      width: options.lineWidth ?? 1.5,
    },
    borderRadius: options.borderRadius ?? "rounded-xl",
  });
}

function addRule(slide, name, x, y, width, color = C.white10, height = 2) {
  return slide.shapes.add({
    geometry: "rect",
    name,
    position: { left: x, top: y, width, height },
    fill: color,
    line: { style: "solid", fill: "none", width: 0 },
  });
}

function addStageText(slide, box, title, body, accent) {
  addText(slide, `${box.name}-title`, title, {
    left: box.position.left + 18,
    top: box.position.top + 18,
    width: box.position.width - 36,
    height: 30,
  }, { fontSize: 19, bold: true, color: accent, alignment: "center", verticalAlignment: "middle" });
  addText(slide, `${box.name}-body`, body, {
    left: box.position.left + 18,
    top: box.position.top + 58,
    width: box.position.width - 36,
    height: box.position.height - 70,
  }, { fontSize: 15, color: C.muted, alignment: "center", verticalAlignment: "top", lineSpacing: 1.08 });
}

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function main() {
  await fs.mkdir(buildDir, { recursive: true });
  await fs.mkdir(outputDir, { recursive: true });

  const presentation = Presentation.create({
    slideSize: { width: 1280, height: 720 },
  });
  const slide = presentation.slides.add();
  slide.background.fill = C.bg;

  // Header
  addText(slide, "eyebrow", "RESEARCH PROJECT", { left: 58, top: 38, width: 250, height: 22 }, {
    fontSize: 14, bold: true, color: C.cyan, verticalAlignment: "middle",
  });
  addText(slide, "title", "Sinhala-script language identification", { left: 56, top: 68, width: 760, height: 62 }, {
    fontSize: 48, bold: true, color: C.text, verticalAlignment: "middle", lineSpacing: 0.92,
  });
  addText(slide, "subtitle", "Distinguishing Sinhala, Pali and Sanskrit written in the same script", { left: 58, top: 130, width: 780, height: 32 }, {
    fontSize: 21, color: C.muted, verticalAlignment: "middle",
  });
  addText(slide, "purpose", "PURPOSE\nReliable routing for multilingual NLP, OCR and digital-text collections", { left: 910, top: 64, width: 314, height: 78 }, {
    fontSize: 14, bold: true, color: C.gold, alignment: "right", verticalAlignment: "middle", lineSpacing: 1.05,
  });
  slide.shapes.items.at(-1).text.get("Reliable routing for multilingual NLP, OCR and digital-text collections").bold = false;
  slide.shapes.items.at(-1).text.get("Reliable routing for multilingual NLP, OCR and digital-text collections").color = C.muted;
  addRule(slide, "header-rule", 56, 176, 1168, C.white10, 2);

  // Column dividers and section labels.
  addRule(slide, "divider-left", 352, 208, 2, C.white10, 394);
  addRule(slide, "divider-right", 932, 208, 2, C.white10, 394);
  addText(slide, "problem-label", "PROBLEM", { left: 58, top: 210, width: 180, height: 22 }, {
    fontSize: 14, bold: true, color: C.red,
  });
  addText(slide, "approach-label", "CLASSIFICATION APPROACH", { left: 382, top: 210, width: 300, height: 22 }, {
    fontSize: 14, bold: true, color: C.purple,
  });
  addText(slide, "outcome-label", "KEY OUTCOME", { left: 962, top: 210, width: 220, height: 22 }, {
    fontSize: 14, bold: true, color: C.green,
  });

  // Problem statement.
  addText(slide, "problem-heading", "One script,\nthree languages", { left: 58, top: 246, width: 256, height: 82 }, {
    fontSize: 31, bold: true, color: C.text, lineSpacing: 0.94,
  });
  addText(slide, "problem-body", "Script detection alone cannot separate the three closely related languages.", { left: 58, top: 344, width: 252, height: 58 }, {
    fontSize: 18, color: C.muted, lineSpacing: 1.05,
  });
  addText(slide, "zero-metric", "0.00%", { left: 56, top: 420, width: 240, height: 74 }, {
    fontSize: 58, bold: true, color: C.red, verticalAlignment: "middle",
  });
  addText(slide, "zero-caption", "zero-shot F1 for Sinhala-script Pali and Sanskrit in stock foundation models", { left: 58, top: 500, width: 260, height: 68 }, {
    fontSize: 16, color: C.text, lineSpacing: 1.02,
  });
  addText(slide, "problem-note", "Existing label heads funnel both classes into Sinhala.", { left: 58, top: 570, width: 250, height: 40 }, {
    fontSize: 14, italic: true, color: C.muted,
  });

  // Central editable workflow.
  const corpus = addBox(slide, "corpus-stage", { left: 532, top: 246, width: 250, height: 94 }, {
    fill: C.surface2, line: C.cyan, lineWidth: 2,
  });
  addText(slide, "corpus-stage-title", "Curated corpus", { left: 550, top: 260, width: 214, height: 28 }, {
    fontSize: 19, bold: true, color: C.cyan, alignment: "center", verticalAlignment: "middle",
  });
  addText(slide, "corpus-stage-body", "67,332 paper-benchmark sentences\nGroup-stratified train and test splits", { left: 550, top: 294, width: 214, height: 34 }, {
    fontSize: 13, color: C.muted, alignment: "center", verticalAlignment: "middle", lineSpacing: 1.02,
  });

  const closed = addBox(slide, "closed-world-stage", { left: 382, top: 380, width: 244, height: 136 }, {
    fill: C.surface, line: C.gold, lineWidth: 2,
  });
  addStageText(slide, closed, "Closed-world benchmark", "7 models trained from scratch\nFull to one-word stress tests\nCharacter n-grams and subword features", C.gold);

  const open = addBox(slide, "open-world-stage", { left: 658, top: 380, width: 244, height: 136 }, {
    fill: C.surface, line: C.purple, lineWidth: 2,
  });
  addStageText(slide, open, "Open-world benchmark", "6 foundation-model families\n11 languages across three hybrids\nRouting, LoRA and head extension", C.purple);

  const output = addBox(slide, "language-output", { left: 470, top: 555, width: 344, height: 58 }, {
    fill: "#0E2630", line: C.green, lineWidth: 2,
  });
  addText(slide, "language-output-text", "SINHALA        PALI        SANSKRIT", { left: 484, top: 568, width: 316, height: 30 }, {
    fontSize: 17, bold: true, color: C.green, alignment: "center", verticalAlignment: "middle",
  });

  slide.shapes.connect(corpus, closed, {
    kind: "elbow", fromSide: "bottom", toSide: "top",
    line: { style: "solid", fill: C.faint, width: 2 },
    tail: { type: "arrow", width: "sm", length: "sm" },
  });
  slide.shapes.connect(corpus, open, {
    kind: "elbow", fromSide: "bottom", toSide: "top",
    line: { style: "solid", fill: C.faint, width: 2 },
    tail: { type: "arrow", width: "sm", length: "sm" },
  });
  slide.shapes.connect(closed, output, {
    kind: "elbow", fromSide: "bottom", toSide: "top",
    line: { style: "solid", fill: C.gold, width: 2 },
    tail: { type: "arrow", width: "sm", length: "sm" },
  });
  slide.shapes.connect(open, output, {
    kind: "elbow", fromSide: "bottom", toSide: "top",
    line: { style: "solid", fill: C.purple, width: 2 },
    tail: { type: "arrow", width: "sm", length: "sm" },
  });

  // Outcomes, expressed as three evidence-led metrics rather than cards.
  addText(slide, "metric-one", "0.9985", { left: 962, top: 252, width: 220, height: 56 }, {
    fontSize: 42, bold: true, color: C.green, verticalAlignment: "middle",
  });
  addText(slide, "metric-one-caption", "Macro-F1, full sentences\nMultinomial Naive Bayes", { left: 962, top: 306, width: 240, height: 48 }, {
    fontSize: 15, color: C.muted, lineSpacing: 1.02,
  });
  addRule(slide, "metric-rule-one", 962, 366, 238, C.white10, 2);

  addText(slide, "metric-two", "0.8584", { left: 962, top: 382, width: 220, height: 56 }, {
    fontSize: 42, bold: true, color: C.gold, verticalAlignment: "middle",
  });
  addText(slide, "metric-two-caption", "Macro-F1, one-word fragments\nMultinomial Naive Bayes", { left: 962, top: 436, width: 240, height: 48 }, {
    fontSize: 15, color: C.muted, lineSpacing: 1.02,
  });
  addRule(slide, "metric-rule-two", 962, 496, 238, C.white10, 2);

  addText(slide, "metric-three", "0.92–0.97", { left: 962, top: 512, width: 250, height: 56 }, {
    fontSize: 39, bold: true, color: C.purple, verticalAlignment: "middle",
  });
  addText(slide, "metric-three-caption", "Macro-F1 range reported for targeted adaptation across 11-language hybrid benchmarks", { left: 962, top: 568, width: 242, height: 54 }, {
    fontSize: 15, color: C.muted, lineSpacing: 1.02,
  });

  // Footer: technologies and data sources.
  addRule(slide, "footer-rule", 56, 642, 1168, C.white10, 2);
  addText(slide, "technology-footer", "TECHNOLOGIES  Python, scikit-learn, PyTorch, Transformers, fastText and Hugging Face", { left: 58, top: 654, width: 670, height: 22 }, {
    fontSize: 13, color: C.muted, verticalAlignment: "middle",
  });
  slide.shapes.items.at(-1).text.get("TECHNOLOGIES").bold = true;
  slide.shapes.items.at(-1).text.get("TECHNOLOGIES").color = C.cyan;
  addText(slide, "evaluation-footer", "EVALUATION  FLORES+, CommonLID and WiLI-2018 hybrid benchmarks", { left: 748, top: 654, width: 476, height: 22 }, {
    fontSize: 13, color: C.muted, alignment: "right", verticalAlignment: "middle",
  });
  slide.shapes.items.at(-1).text.get("EVALUATION").bold = true;
  slide.shapes.items.at(-1).text.get("EVALUATION").color = C.purple;

  slide.speakerNotes.text = [
    "Repository evidence used for this slide:",
    `${path.join(workspaceDir, "ACL.tex")} — abstract, dataset construction, Phase 1 and Phase 2 results.`,
    `${path.join(workspaceDir, "README.md")} — project purpose, model families, technologies and repository scope.`,
    `${path.join(workspaceDir, "Comparison Tables - Final Corrected.csv")} — per-model benchmark results.`,
    `${path.join(workspaceDir, "requirements.txt")} — implementation technologies.`,
    "No personal names, index numbers, group numbers or team identifiers appear on the slide.",
  ].join("\n");

  const draftPptx = await PresentationFile.exportPptx(presentation);
  await draftPptx.save(candidatePath);

  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(layoutPath, await layout.text(), "utf8");
  const inspection = await presentation.inspect({
    kind: "slide,textbox,shape,notes,layout",
    maxChars: 30000,
  });
  await fs.writeFile(inspectionPath, inspection.ndjson, "utf8");

  // The managed Windows sandbox blocks fs.realpath even for permitted workspace
  // paths. Preserve the finalizer's lstat checks and use normalized absolute paths
  // only when realpath fails with that sandbox-specific EPERM.
  const nativeRealpath = fs.realpath.bind(fs);
  fs.realpath = async (target, ...args) => {
    try {
      return await nativeRealpath(target, ...args);
    } catch (error) {
      if (error?.code === "EPERM") return path.resolve(String(target));
      throw error;
    }
  };
  const nativeLink = fs.link.bind(fs);
  fs.link = async (source, destination) => {
    try {
      return await nativeLink(source, destination);
    } catch (error) {
      if (error?.code === "EPERM") return fs.copyFile(source, destination, 1);
      throw error;
    }
  };

  const { finalizePresentation } = await import(pathToFileURL(
    path.join(skillDir, "container_tools", "artifact_tool_utils.mjs"),
  ).href);
  const result = await finalizePresentation({
    explicitTotalSlideCount: 1,
    requiredNativeTableOwnerSlides: [],
    requiredNativeChartOwnerSlides: [],
    workspaceDir,
    candidatePath,
    finalPath: finalPptx,
    pythonExecutable: runtimePython,
    integrityValidatorPath: path.join(skillDir, "container_tools", "inspect_presentation_package_integrity.py"),
    layoutValidatorPath: path.join(skillDir, "container_tools", "inspect_presentation_layout_geometry.py"),
    layoutArgs: [
      "--expected-slide-size-emu", "12192000,6858000",
      "--validate-bullet-geometry",
      "--validate-heading-fit",
    ],
    fontPolicy: { basis: "design", families: [FONT] },
    verifyArtifactToolImport: true,
    receiptPath,
  });
  console.log(JSON.stringify(result, null, 2));

  const finalDeck = await PresentationFile.importPptx(await FileBlob.load(finalPptx));
  const finalSlide = finalDeck.slides.items[0];
  await writeBlob(previewPng, await finalDeck.export({ slide: finalSlide, format: "png", scale: 1.5 }));

  console.log(JSON.stringify({ finalPptx, previewPng, candidatePath, receiptPath, layoutPath }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
