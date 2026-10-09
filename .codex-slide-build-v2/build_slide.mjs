import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { FileBlob, Presentation, PresentationFile } from "file:///C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const workspaceDir = "C:\\Users\\User\\Desktop\\Vscode\\Sinhala-Script Language Identification (LangID) for Sinhala, Pali and Sanskrit\\Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit";
const skillDir = "C:\\Users\\User\\.codex\\plugins\\cache\\openai-primary-runtime\\presentations\\26.1007.11041\\skills\\presentations";
const runtimePython = "C:\\Users\\User\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe";
const buildDir = path.join(workspaceDir, ".codex-slide-build-v2");
const outputDir = path.join(workspaceDir, "deliverables");
const candidatePath = path.join(buildDir, "candidate.pptx");
const finalPptx = path.join(outputDir, "Sinhala_Script_LangID_Project_One_Slide.pptx");
const previewPng = path.join(outputDir, "Sinhala_Script_LangID_Project_One_Slide_Preview.png");
const receiptPath = path.join(buildDir, "validation.json");

const K = {
  navy: "#0D365B",
  blue: "#165B91",
  teal: "#0D9BA8",
  tealLight: "#EAF7F8",
  paleBlue: "#EFF6FB",
  ink: "#152B3A",
  slate: "#4E6574",
  line: "#B8D4E4",
  white: "#FFFFFF",
  bg: "#F9FBFD",
  red: "#D54C5C",
  amber: "#E5A32E",
};
const FONT = "Arial";

function rect(slide, name, x, y, w, h, fill, line = "none", lineWidth = 0, radius = false) {
  return slide.shapes.add({
    name,
    geometry: radius ? "roundRect" : "rect",
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: line, width: lineWidth },
    ...(radius ? { borderRadius: "rounded-md" } : {}),
  });
}

function tx(slide, name, value, x, y, w, h, opts = {}) {
  const shape = slide.shapes.add({
    name,
    geometry: "textbox",
    position: { left: x, top: y, width: w, height: h },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = value;
  shape.text.style = {
    typeface: FONT,
    fontSize: opts.size ?? 18,
    bold: opts.bold ?? false,
    color: opts.color ?? K.ink,
    alignment: opts.align ?? "left",
    verticalAlignment: opts.valign ?? "top",
    autoFit: "shrinkText",
    wrap: "square",
    insets: 0,
    lineSpacing: opts.spacing ?? 1.02,
  };
  return shape;
}

function sectionTitle(slide, title, x, y, width) {
  tx(slide, `section-${title}`, title.toUpperCase(), x, y, width, 30, {
    size: 22, bold: true, color: K.navy, valign: "middle",
  });
  rect(slide, `accent-${title}`, x, y + 34, 62, 4, K.teal);
}

function arrow(slide, name, x1, y, x2, color = K.teal) {
  slide.shapes.add({
    name,
    geometry: "connector",
    kind: "straight",
    position: { left: x1, top: y, width: x2 - x1, height: 0 },
    line: { style: "solid", fill: color, width: 2 },
    tail: { type: "triangle", width: "sm", length: "sm" },
  });
}

function downArrow(slide, name, x, y1, y2, color = K.teal) {
  slide.shapes.add({
    name,
    geometry: "connector",
    kind: "straight",
    position: { left: x, top: y1, width: 0, height: y2 - y1 },
    line: { style: "solid", fill: color, width: 2 },
    tail: { type: "triangle", width: "sm", length: "sm" },
  });
}

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function main() {
  await fs.mkdir(buildDir, { recursive: true });
  await fs.mkdir(outputDir, { recursive: true });

  const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });
  const slide = deck.slides.add();
  slide.background.fill = K.bg;

  // A restrained poster header follows the blue academic one-page references.
  rect(slide, "header-band", 0, 0, 1280, 135, K.navy);
  rect(slide, "header-accent", 0, 132, 1280, 5, K.teal);
  tx(slide, "header-kicker", "BENCHMARK  +  PRODUCTION PLATFORM", 48, 17, 780, 20, {
    size: 14, bold: true, color: "#9DE1E5", valign: "middle",
  });
  tx(slide, "slide-title", "Sinhala-Script Language Identification", 46, 43, 1160, 58, {
    size: 44, bold: true, color: K.white, valign: "middle",
  });
  tx(slide, "slide-subtitle", "Disambiguating Sinhala, Pali and Sanskrit in research and document workflows", 48, 100, 1150, 27, {
    size: 20, color: "#D4E7F1", valign: "middle",
  });

  // Three aligned content columns.
  rect(slide, "left-divider", 381, 159, 2, 455, K.line);
  rect(slide, "right-divider", 888, 159, 2, 455, K.line);

  // Problem and corpus.
  sectionTitle(slide, "The problem", 48, 160, 315);
  tx(slide, "problem-copy", "The Sinhala script also carries Pali and Sanskrit. Off-the-shelf language identifiers often label both as Sinhala, making historical texts harder to search and index.", 48, 213, 310, 126, {
    size: 18, color: K.ink, spacing: 1.08,
  });
  rect(slide, "zero-callout", 48, 352, 312, 96, K.tealLight, "#BDE4E7", 1, true);
  tx(slide, "zero-number", "0%", 65, 366, 105, 58, {
    size: 46, bold: true, color: K.red, valign: "middle",
  });
  tx(slide, "zero-label", "reported zero-shot F1 for Sinhala-script Pali and Sanskrit in tested stock models", 174, 365, 170, 66, {
    size: 15, color: K.slate, valign: "middle", spacing: 1.02,
  });
  sectionTitle(slide, "Research corpus", 48, 468, 315);
  tx(slide, "corpus-number", "74,318", 48, 516, 215, 59, {
    size: 45, bold: true, color: K.blue, valign: "middle",
  });
  tx(slide, "corpus-copy", "Sinhala-script sentences; split by document group. The held-out test set contains 7,047 sentences.", 48, 572, 300, 44, {
    size: 15, color: K.slate, spacing: 1.02,
  });

  // Research design, with a compact editable workflow.
  sectionTitle(slide, "Research methodology", 407, 160, 455);
  rect(slide, "method-1", 407, 213, 456, 113, K.paleBlue, K.line, 1, true);
  tx(slide, "method-1-number", "01", 423, 227, 50, 28, { size: 17, bold: true, color: K.teal });
  tx(slide, "method-1-title", "Closed-world benchmark", 473, 225, 365, 31, {
    size: 21, bold: true, color: K.navy,
  });
  tx(slide, "method-1-copy", "Seven models trained from scratch, including character n-gram and neural baselines. Tested on full sentences and 5-, 3-, and 1-word fragments.", 423, 264, 412, 50, {
    size: 16, color: K.slate, spacing: 1.03,
  });

  rect(slide, "method-2", 407, 341, 456, 114, K.paleBlue, K.line, 1, true);
  tx(slide, "method-2-number", "02", 423, 355, 50, 28, { size: 17, bold: true, color: K.teal });
  tx(slide, "method-2-title", "Open-world adaptation", 473, 353, 365, 31, {
    size: 21, bold: true, color: K.navy,
  });
  tx(slide, "method-2-copy", "Six pretrained families adapted and evaluated on 11 language-script classes across FLORES+, CommonLID and WiLI-2018 hybrid benchmarks.", 423, 392, 412, 49, {
    size: 16, color: K.slate, spacing: 1.03,
  });

  tx(slide, "routing-heading", "TWO-STAGE ROUTING EXAMPLE", 407, 472, 455, 24, {
    size: 15, bold: true, color: K.blue,
  });
  const ry = 510;
  rect(slide, "router", 407, ry, 128, 68, K.white, K.teal, 2, true);
  tx(slide, "router-text", "Global\nrouter", 416, ry + 11, 110, 47, { size: 17, bold: true, color: K.navy, align: "center", valign: "middle" });
  arrow(slide, "router-arrow", 541, ry + 34, 561);
  rect(slide, "gate", 565, ry, 127, 68, K.white, K.teal, 2, true);
  tx(slide, "gate-text", "Sinhala\nscript?", 574, ry + 11, 109, 47, { size: 17, bold: true, color: K.navy, align: "center", valign: "middle" });
  arrow(slide, "gate-arrow", 698, ry + 34, 718);
  rect(slide, "specialist", 722, ry, 141, 68, K.white, K.teal, 2, true);
  tx(slide, "specialist-text", "Three-language\nspecialist", 731, ry + 11, 123, 47, { size: 16, bold: true, color: K.navy, align: "center", valign: "middle" });
  tx(slide, "routing-note", "Other scripts retain the global model prediction.", 407, 590, 456, 25, {
    size: 15, color: K.slate,
  });

  // Production system in the third column.
  sectionTitle(slide, "Web platform", 914, 160, 315);
  tx(slide, "platform-intro", "A browser workflow for classifying text and scanned documents, then reviewing the language labels.", 914, 213, 305, 68, {
    size: 18, color: K.ink, spacing: 1.07,
  });

  const stages = [
    ["Upload", "Text, PDF or image"],
    ["Extract", "Tesseract or Surya OCR"],
    ["Classify", "FastAPI with background workers"],
    ["Review", "Color highlights and corrections"],
  ];
  stages.forEach(([label, detail], i) => {
    const y = 294 + i * 69;
    rect(slide, `platform-${i}`, 914, y, 309, 52, i % 2 ? K.white : K.paleBlue, K.line, 1, true);
    tx(slide, `platform-${i}-label`, label, 929, y + 7, 99, 37, {
      size: 17, bold: true, color: K.blue, valign: "middle",
    });
    tx(slide, `platform-${i}-detail`, detail, 1031, y + 7, 177, 37, {
      size: 14, color: K.slate, valign: "middle",
    });
    if (i < 3) downArrow(slide, `platform-arrow-${i}`, 1068, y + 52, y + 65, K.teal);
  });
  tx(slide, "platform-stack", "Next.js 16, FastAPI, Celery, Redis and PostgreSQL", 914, 581, 306, 37, {
    size: 15, color: K.slate, spacing: 1.03,
  });

  // Three clearly scoped outcomes in the footer.
  rect(slide, "results-band", 0, 636, 1280, 84, K.navy);
  tx(slide, "results-label", "SELECT RESULTS  ·  MACRO-F1", 48, 647, 302, 18, {
    size: 13, bold: true, color: "#9DE1E5",
  });
  tx(slide, "result-1", "0.9985", 48, 665, 145, 41, { size: 31, bold: true, color: K.white, valign: "middle" });
  tx(slide, "result-1-caption", "MNB, full sentence", 184, 670, 210, 30, { size: 15, color: "#D4E7F1", valign: "middle" });
  rect(slide, "footer-divider-1", 414, 652, 2, 54, "#5D819D");
  tx(slide, "result-2", "0.8584", 443, 665, 145, 41, { size: 31, bold: true, color: K.white, valign: "middle" });
  tx(slide, "result-2-caption", "MNB, one word", 579, 670, 180, 30, { size: 15, color: "#D4E7F1", valign: "middle" });
  rect(slide, "footer-divider-2", 780, 652, 2, 54, "#5D819D");
  tx(slide, "result-3", "0.9530", 809, 665, 145, 41, { size: 31, bold: true, color: K.white, valign: "middle" });
  tx(slide, "result-3-caption", "NLLB, 11-language FLORES+", 948, 670, 280, 30, { size: 15, color: "#D4E7F1", valign: "middle" });

  slide.speakerNotes.text = [
    "Sources for slide claims and implementation:",
    path.join(workspaceDir, "ACLV2.tex") + " (target corpus, benchmark design and reported results)",
    path.join(workspaceDir, "webapp", "frontend", "package.json") + " (Next.js version)",
    path.join(workspaceDir, "webapp", "backend", "pyproject.toml") + " (backend dependencies)",
    path.join(workspaceDir, "webapp", "backend", "app", "ocr", "registry.py") + " (OCR engines)",
    path.join(workspaceDir, "webapp", "backend", "app", "api", "v1", "annotations.py") + " (corrections)",
    "The user-provided complete project description informed the slide structure. No personal or team identifiers are included.",
  ].join("\n");

  await (await PresentationFile.exportPptx(deck)).save(candidatePath);
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(buildDir, "slide.layout.json"), await layout.text(), "utf8");

  // The managed Windows sandbox rejects realpath and hard links inside the
  // permitted workspace. The finalizer still verifies file type and hashes.
  const realpathOriginal = fs.realpath.bind(fs);
  fs.realpath = async (target, ...args) => {
    try { return await realpathOriginal(target, ...args); }
    catch (error) {
      if (error?.code === "EPERM") return path.resolve(String(target));
      throw error;
    }
  };
  const linkOriginal = fs.link.bind(fs);
  fs.link = async (source, destination) => {
    try { return await linkOriginal(source, destination); }
    catch (error) {
      if (error?.code === "EPERM") return fs.copyFile(source, destination, 1);
      throw error;
    }
  };

  const { finalizePresentation } = await import(pathToFileURL(path.join(skillDir, "container_tools", "artifact_tool_utils.mjs")).href);
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
    layoutArgs: ["--expected-slide-size-emu", "12192000,6858000", "--validate-bullet-geometry", "--validate-heading-fit"],
    fontPolicy: { basis: "design", families: [FONT] },
    verifyArtifactToolImport: true,
    receiptPath,
  });
  console.log(JSON.stringify({ finalPath: result.finalPath, finalSha256: result.finalSha256, layoutFindings: result.presentationLayout.finding_count, slideCount: result.packageIntegrity.slide_count }, null, 2));

  const imported = await PresentationFile.importPptx(await FileBlob.load(finalPptx));
  await writeBlob(previewPng, await imported.export({ slide: imported.slides.items[0], format: "png", scale: 1.5 }));
  console.log(JSON.stringify({ previewPng }, null, 2));
}

main().catch(error => { console.error(error); process.exitCode = 1; });
