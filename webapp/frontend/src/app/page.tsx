import Link from "next/link";
import { Noto_Sans_Sinhala } from "next/font/google";
import {
  ArrowRight,
  BookOpen,
  Check,
  Coins,
  Database,
  Download,
  FileText,
  GraduationCap,
  Landmark,
  Languages,
  Layers,
  MessageSquareWarning,
  MousePointerClick,
  RefreshCw,
  ScanText,
  Sparkles,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { AppHeader } from "@/components/layout/app-header";
import { Logo } from "@/components/layout/logo";
import { Screenshot } from "@/components/landing/screenshot";
import { cn } from "@/lib/utils";

import classifyResult from "@/assets/landing/classify-result.webp";
import classifyInput from "@/assets/landing/classify-input.webp";
import classifyFocus from "@/assets/landing/classify-focus.webp";
import classifyTooltip from "@/assets/landing/classify-tooltip.webp";
import classifyCorrect from "@/assets/landing/classify-correct.webp";
import docDone from "@/assets/landing/doc-done.webp";
import uploadModal from "@/assets/landing/upload-modal.webp";
import dashboard from "@/assets/landing/dashboard.webp";

const sinhala = Noto_Sans_Sinhala({ subsets: ["sinhala"], display: "swap" });

// One passage, three languages, all in Sinhala script (from the demo text).
const PASSAGE = [
  { text: "ධම්මපදය බෞද්ධ සාහිත්‍යයේ වඩාත් ප්‍රසිද්ධ ග්‍රන්ථයකි.", lang: "Sinhala", mark: "bg-blue-100 text-blue-900", chip: "bg-blue-50 border-blue-300 text-blue-800" },
  { text: "මනොපුබ්බඞ්ගමා ධම්මා මනොසෙට්ඨා මනොමයා.", lang: "Pali", mark: "bg-emerald-100 text-emerald-900", chip: "bg-emerald-50 border-emerald-300 text-emerald-800" },
  { text: "මාමකාඃ පාණ්ඩවාශ්චෛව කිමකුර්වත සඤ්ජය.", lang: "Sanskrit", mark: "bg-violet-100 text-violet-900", chip: "bg-violet-50 border-violet-300 text-violet-800" },
];

// F1 on the held-out target test set: GlotLID v3 as released (zero-shot) and
// after fine-tuning with rehearsal (data_pipeline benchmark tables 1 and 3).
const GAP = [
  { lang: "Sinhala", before: 0.716, after: 0.9993, bar: "bg-blue-500" },
  { lang: "Pali", before: 0, after: 0.9992, bar: "bg-emerald-500" },
  { lang: "Sanskrit", before: 0, after: 0.9992, bar: "bg-violet-500" },
];

// Table 3 (rehearsal), held-out target test set, per-language F1.
const MODELS = [
  { name: "OpenLID v3", macro: 0.9996, sin: 0.9994, pli: 0.9992, san: 1.0 },
  { name: "NLLB LID-218", macro: 0.9995, sin: 0.9995, pli: 0.9994, san: 0.9996 },
  { name: "GlotLID v3", macro: 0.9992, sin: 0.9993, pli: 0.9992, san: 0.9992 },
  { name: "fastText LID-176", macro: 0.9979, sin: 0.9988, pli: 0.9982, san: 0.9966 },
  { name: "ConLID", macro: 0.9844, sin: 0.9933, pli: 0.9907, san: 0.9693 },
];

const pct = (x: number) => (x === 1 ? "100%" : `${(x * 100).toFixed(2)}%`);

function Eyebrow({ children, dark }: { children: React.ReactNode; dark?: boolean }) {
  return (
    <p className={cn("mb-3 text-xs font-semibold uppercase tracking-[0.18em]", dark ? "text-blue-300" : "text-primary")}>
      {children}
    </p>
  );
}

function Feature({
  eyebrow,
  title,
  body,
  points,
  children,
  flip,
}: {
  eyebrow: string;
  title: string;
  body: string;
  points: string[];
  children: React.ReactNode;
  flip?: boolean;
}) {
  return (
    <div className="grid grid-cols-1 items-center gap-10 lg:grid-cols-12 lg:gap-14">
      <div className={cn("min-w-0 lg:col-span-5", flip && "lg:order-2")}>
        <Eyebrow>{eyebrow}</Eyebrow>
        <h3 className="mb-4 text-2xl font-bold tracking-tight sm:text-3xl">{title}</h3>
        <p className="mb-6 leading-relaxed text-muted-foreground">{body}</p>
        <ul className="space-y-3">
          {points.map((p) => (
            <li key={p} className="flex gap-3 text-sm">
              <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
              <span>{p}</span>
            </li>
          ))}
        </ul>
      </div>
      <div className={cn("min-w-0 lg:col-span-7", flip && "lg:order-1")}>{children}</div>
    </div>
  );
}

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <AppHeader />

      <main className="flex-1">
        {/* Hero */}
        <section className="relative overflow-hidden pt-16 sm:pt-24">
          <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_80%_60%_at_50%_-10%,rgba(59,130,246,0.16),transparent)]" />
          <div className="absolute inset-x-0 top-0 -z-10 h-[38rem] bg-[linear-gradient(to_right,rgba(148,163,184,0.12)_1px,transparent_1px),linear-gradient(to_bottom,rgba(148,163,184,0.12)_1px,transparent_1px)] bg-[size:48px_48px] [mask-image:radial-gradient(ellipse_70%_60%_at_50%_0%,#000_40%,transparent_100%)]" />

          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-4xl text-center">
              <div className={cn("mb-6 flex flex-wrap items-center justify-center gap-2 text-sm", sinhala.className)}>
                <span className="rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-blue-800">සිංහල</span>
                <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-emerald-800">පාළි</span>
                <span className="rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-violet-800">සංස්කෘත</span>
              </div>

              <h1 className="mb-6 text-4xl font-extrabold tracking-tight text-foreground sm:text-6xl">
                One script. Three languages.
                <br />
                <span className="bg-gradient-to-r from-blue-600 via-emerald-500 to-violet-600 bg-clip-text text-transparent">
                  Finally told apart.
                </span>
              </h1>

              <p className="mx-auto mb-10 max-w-2xl text-lg leading-relaxed text-muted-foreground">
                Sinhala, Pali and Sanskrit share the same letters and often the same page. Today&apos;s language identifiers
                see Sinhala script and answer &ldquo;Sinhala&rdquo;. LangID tells you, sentence by sentence, which language
                you&apos;re actually reading, in pasted text or scanned PDFs.
              </p>

              <div className="flex flex-wrap items-center justify-center gap-4">
                <Link href="/auth/signup">
                  <Button size="lg" className="group h-12 px-8 text-base shadow-md transition-shadow hover:shadow-lg">
                    Start identifying for free
                    <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                  </Button>
                </Link>
                <a href="#tour">
                  <Button size="lg" variant="outline" className="h-12 border-primary/30 px-8 text-base text-primary hover:bg-primary/5">
                    See it in action
                  </Button>
                </a>
              </div>

              <dl className="mx-auto mt-12 grid max-w-3xl grid-cols-2 gap-6 sm:grid-cols-4">
                {[
                  ["99.9%", "F1 on Sinhala, Pali & Sanskrit"],
                  ["0 → 99.9%", "Pali & Sanskrit, vs. off-the-shelf"],
                  ["2,100+", "other languages still recognised by GlotLID"],
                  ["6", "models to choose from"],
                ].map(([value, label]) => (
                  <div key={label}>
                    <dt className="sr-only">{label}</dt>
                    <dd className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">{value}</dd>
                    <dd className="mt-1 text-xs text-muted-foreground">{label}</dd>
                  </div>
                ))}
              </dl>
            </div>

            <div className="relative mx-auto mt-16 max-w-6xl">
              <Screenshot
                src={classifyResult}
                alt="LangID classification result: a mixed passage with Sinhala sentences highlighted in blue, Pali in green, Sanskrit in violet, and English, Tamil and Hindi in their own colours, above a bar showing each language's share."
                url="LangID · Classification results"
                sizes="(min-width: 1280px) 1152px, 100vw"
                preload
              />
              <div className="pointer-events-none absolute -left-6 top-[62%] hidden rounded-xl border bg-white/95 px-4 py-3 shadow-xl backdrop-blur lg:block">
                <p className="text-xs text-muted-foreground">Every sentence</p>
                <p className="text-sm font-semibold">Language + confidence</p>
              </div>
              <div className="pointer-events-none absolute -right-6 top-[38%] hidden rounded-xl border bg-white/95 px-4 py-3 shadow-xl backdrop-blur lg:block">
                <p className="text-xs text-muted-foreground">Original layout</p>
                <p className="text-sm font-semibold">Preserved line by line</p>
              </div>
            </div>
          </div>
          <div className="h-20 bg-gradient-to-b from-transparent to-white sm:h-28" />
        </section>

        {/* The gap */}
        <section id="problem" className="scroll-mt-20 bg-slate-950 py-20 text-white sm:py-28">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-3xl text-center">
              <Eyebrow dark>The gap</Eyebrow>
              <h2 className="mb-5 text-3xl font-bold tracking-tight sm:text-4xl">
                For a reader, it&apos;s natural. For a computer, it&apos;s a puzzle.
              </h2>
              <p className="text-lg leading-relaxed text-slate-300">
                For more than two thousand years one script has carried three languages: Sinhala, the living language of
                Sri Lanka; Pali, the language of the Buddha&apos;s teachings; and Sanskrit, the classical language of
                learning. A Sinhala commentary quotes a Pali verse, then a line of Sanskrit, all in the same letters.
              </p>
            </div>

            <div className="mx-auto mt-14 grid max-w-6xl gap-6 lg:grid-cols-2">
              {/* Same page, before and after */}
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 sm:p-8">
                <p className="mb-5 text-sm font-medium text-slate-400">Same script. Same page. Three languages.</p>
                <div className={cn("space-y-3 text-lg leading-relaxed text-slate-400", sinhala.className)}>
                  {PASSAGE.map((s) => (
                    <p key={s.lang}>{s.text}</p>
                  ))}
                </div>
                <div className="my-6 flex items-center gap-3 text-xs font-semibold uppercase tracking-wider text-blue-300">
                  <span className="h-px flex-1 bg-white/10" />
                  With LangID
                  <span className="h-px flex-1 bg-white/10" />
                </div>
                <div className={cn("space-y-3 text-base leading-relaxed", sinhala.className)}>
                  {PASSAGE.map((s) => (
                    <p key={s.lang} className="flex items-start justify-between gap-3">
                      <span className={cn("rounded px-1", s.mark)}>{s.text}</span>
                      <span className={cn("mt-1 shrink-0 rounded-full border px-2 py-0.5 font-sans text-xs font-medium", s.chip)}>{s.lang}</span>
                    </p>
                  ))}
                </div>
              </div>

              {/* Before / after chart */}
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 sm:p-8">
                <p className="mb-1 text-sm font-medium text-slate-400">F1 score on a held-out test set (GlotLID v3)</p>
                <div className="mb-6 flex flex-wrap gap-4 text-xs text-slate-400">
                  <span className="flex items-center gap-1.5"><span className="h-2 w-4 rounded-sm bg-slate-600" />Off-the-shelf</span>
                  <span className="flex items-center gap-1.5"><span className="h-2 w-4 rounded-sm bg-gradient-to-r from-blue-500 via-emerald-500 to-violet-500" />With LangID</span>
                </div>
                <div className="space-y-6">
                  {GAP.map((g) => (
                    <div key={g.lang}>
                      <p className="mb-2 text-sm font-semibold">{g.lang}</p>
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-3">
                          <div className="h-3 flex-1 overflow-hidden rounded-full bg-white/5">
                            <div className="h-full rounded-full bg-slate-600" style={{ width: `${g.before * 100}%` }} />
                          </div>
                          <span className={cn("w-14 text-right font-mono text-sm tabular-nums", g.before === 0 ? "font-bold text-rose-400" : "text-slate-400")}>
                            {g.before.toFixed(2)}
                          </span>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="h-3 flex-1 overflow-hidden rounded-full bg-white/5">
                            <div className={cn("h-full rounded-full", g.bar)} style={{ width: `${g.after * 100}%` }} />
                          </div>
                          <span className="w-14 text-right font-mono text-sm font-semibold tabular-nums text-white">{g.after.toFixed(3)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <p className="mt-6 text-sm leading-relaxed text-slate-400">
                  Every leading open language identifier we tested scored <strong className="text-rose-400">zero</strong> on
                  Pali and Sanskrit: it labels them all as Sinhala. LangID&apos;s fine-tuned models get them right.
                </p>
              </div>
            </div>

            <div className="mx-auto mt-14 grid max-w-6xl gap-6 md:grid-cols-3">
              {[
                {
                  icon: Database,
                  title: "Corpora stay contaminated",
                  body: "Web-scale datasets filter by language ID. Pali and Sanskrit in Sinhala script quietly end up labelled as Sinhala, polluting all three.",
                },
                {
                  icon: Landmark,
                  title: "Archives can't be searched",
                  body: "Digitised books, journals and transcribed palm-leaf manuscripts mix the three languages. Without labels, nobody can find the verses inside.",
                },
                {
                  icon: BookOpen,
                  title: "Scholars work by hand",
                  body: "Knowing where the Pali starts and the Sinhala ends still means reading every line. LangID does the first pass in seconds.",
                },
              ].map(({ icon: Icon, title, body }) => (
                <div key={title} className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
                  <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/15">
                    <Icon className="h-5 w-5 text-blue-300" />
                  </div>
                  <h3 className="mb-2 font-semibold">{title}</h3>
                  <p className="text-sm leading-relaxed text-slate-400">{body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* How it works */}
        <section id="how" className="scroll-mt-20 py-20 sm:py-28">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="mx-auto mb-14 max-w-2xl text-center">
              <Eyebrow>How it works</Eyebrow>
              <h2 className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl">Three steps from page to languages</h2>
              <p className="text-muted-foreground">No setup, no code. Bring a passage or a whole book.</p>
            </div>
            <ol className="mx-auto grid max-w-5xl gap-6 md:grid-cols-3">
              {[
                { icon: FileText, title: "Bring your text", body: "Paste a passage, or upload a scanned PDF. OCR reads Sinhala, Sanskrit and English pages for you." },
                { icon: Languages, title: "Every sentence identified", body: "LangID splits the text and identifies the language of each sentence, with a confidence score." },
                { icon: Download, title: "Read, correct, export", body: "Explore colour-coded results, fix anything that's wrong, and export everything as CSV." },
              ].map(({ icon: Icon, title, body }, i) => (
                <li key={title} className="relative rounded-2xl border bg-white p-6 shadow-sm">
                  <span className="absolute right-5 top-4 text-5xl font-extrabold text-primary/10">{i + 1}</span>
                  <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-md">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="mb-2 font-semibold">{title}</h3>
                  <p className="text-sm leading-relaxed text-muted-foreground">{body}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* Product tour */}
        <section id="tour" className="scroll-mt-20 border-t bg-secondary/30 py-20 sm:py-28">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="mx-auto mb-16 max-w-2xl text-center">
              <Eyebrow>Product tour</Eyebrow>
              <h2 className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl">See what&apos;s really on the page</h2>
              <p className="text-muted-foreground">Real screens from LangID, running on a real mixed-language passage.</p>
            </div>

            <div className="mx-auto max-w-6xl space-y-24">
              <Feature
                eyebrow="Classify text"
                title="Paste any Sinhala-script text, pick a model"
                body="Choose from six models: a fast three-way baseline, and five leading open language identifiers (NLLB, GlotLID, OpenLID, ConLID and fastText), each fine-tuned on Sinhala, Pali and Sanskrit."
                points={[
                  "Trained with rehearsal, so they still recognise hundreds of other languages (over 2,000 with GlotLID)",
                  "Split by sentence, paragraph, full text, or automatically",
                  "Long passages stream back batch by batch",
                ]}
              >
                <Screenshot src={classifyInput} alt="The Language Identification page: a text box with a mixed passage, and cards for the six models with GlotLID v3 selected." url="LangID · Language ID" />
              </Feature>

              <Feature
                flip
                eyebrow="Read the results"
                title="Every language at a glance"
                body="Your text keeps its original layout, and every sentence is highlighted in its language's colour: blue for Sinhala, green for Pali, violet for Sanskrit. Click a language to fade everything else out."
                points={[
                  "Distribution bar shows how much of the text is in each language",
                  "Focus on one language to find every Pali verse instantly",
                  "English, Tamil, Hindi and others get colours of their own",
                ]}
              >
                <Screenshot src={classifyFocus} alt="Results focused on Pali: the three Pali verse lines stay highlighted in green while all other sentences fade to grey." url="LangID · Classification results" />
              </Feature>

              <Feature
                eyebrow="Confidence"
                title="Know exactly how sure the model is"
                body="Hover any sentence to see its confidence and how the probability is spread across candidate languages. Uncertain sentences get a dashed underline, so you know where to look twice."
                points={["Per-sentence confidence score", "Top candidate languages with probabilities", "Export sentence, language and confidence as CSV"]}
              >
                <Screenshot src={classifyTooltip} alt="A tooltip over a Sanskrit line showing Sanskrit 75.4%, Sinhala 14.7% and Pali 9.9%." url="LangID · Classification results" />
              </Feature>

              <Feature
                flip
                eyebrow="Documents"
                title="From scanned page to languages"
                body="Upload a scanned PDF and LangID reads it page by page with OCR, then identifies the language of every sentence on every page. Results appear as each page finishes, so even whole books are never a long wait."
                points={[
                  "Tesseract for speed, or Surya's transformer OCR for harder scans",
                  "Original page beside the classified text; two-column pages kept in reading order",
                  "Cancel anytime: finished pages are kept and the rest is refunded",
                ]}
              >
                <div className="relative">
                  <Screenshot src={docDone} alt="A 16-page document: language summary bar, page list with each page's main language, and page 1's scan beside its colour-coded text." url="LangID · Documents" />
                  <div className="absolute -bottom-10 -left-4 hidden w-64 sm:block lg:-left-10">
                    <Screenshot src={uploadModal} alt="Upload dialog with Tesseract and Surya OCR engines and a language model picker." url="Upload" sizes="256px" />
                  </div>
                </div>
              </Feature>

              <Feature
                eyebrow="Better with every correction"
                title="Spot a mistake? Teach the model."
                body="No model is perfect. Click any sentence, choose the right language and submit. Corrections go to a review queue and, once approved, become training data for the next version of the models."
                points={["Report → review → approve → retrain", "Admins export the approved set for retraining", "The more LangID is used, the better it gets"]}
              >
                <Screenshot src={classifyCorrect} alt="The Report Misclassification popover open on a Sanskrit line the model read as Sinhala, with a language picker and comment box." url="LangID · Classification results" />
              </Feature>
            </div>

            {/* Smaller capabilities */}
            <div className="mx-auto mt-24 grid max-w-6xl grid-cols-2 gap-4 md:grid-cols-4">
              {[
                { icon: Sparkles, label: "Six models to compare" },
                { icon: ScanText, label: "Two OCR engines" },
                { icon: Layers, label: "Live, page-by-page results" },
                { icon: MousePointerClick, label: "Focus by language" },
                { icon: MessageSquareWarning, label: "Corrections feed retraining" },
                { icon: Download, label: "CSV export" },
                { icon: RefreshCw, label: "Cancel and refund" },
                { icon: Coins, label: "Pay only for what you use" },
              ].map(({ icon: Icon, label }) => (
                <div key={label} className="flex items-center gap-3 rounded-xl border bg-white p-4 text-sm font-medium shadow-sm">
                  <Icon className="h-4 w-4 shrink-0 text-primary" />
                  {label}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Research */}
        <section id="research" className="scroll-mt-20 py-20 sm:py-28">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="mx-auto grid max-w-6xl grid-cols-1 gap-12 lg:grid-cols-12">
              <div className="min-w-0 lg:col-span-5">
                <Eyebrow>Built on research</Eyebrow>
                <h2 className="mb-5 text-3xl font-bold tracking-tight sm:text-4xl">Near-perfect, without forgetting the rest of the world</h2>
                <p className="mb-6 leading-relaxed text-muted-foreground">
                  LangID grew out of a dedicated study of Sinhala-script language identification. Each model was
                  fine-tuned on a carefully built, leakage-free dataset of Sinhala, Pali and Sanskrit, and trained with
                  rehearsal so it keeps recognising the languages it already knew.
                </p>
                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-xl border bg-secondary/40 p-4">
                    <p className="text-3xl font-bold tracking-tight text-primary">99.96%</p>
                    <p className="mt-1 text-xs text-muted-foreground">best macro-F1 on Sinhala, Pali &amp; Sanskrit</p>
                  </div>
                  <div className="rounded-xl border bg-secondary/40 p-4">
                    <p className="text-3xl font-bold tracking-tight text-primary">≥ 99.4%</p>
                    <p className="mt-1 text-xs text-muted-foreground">macro-F1 on the FLORES+ benchmark, after fine-tuning</p>
                  </div>
                </div>
              </div>

              <div className="min-w-0 lg:col-span-7">
                <div className="overflow-hidden rounded-2xl border shadow-sm">
                  <div className="border-b bg-slate-50 px-5 py-3">
                    <p className="text-sm font-semibold">F1 per language, held-out test set</p>
                    <p className="text-xs text-muted-foreground">Fine-tuned with rehearsal</p>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b text-left text-xs uppercase tracking-wider text-muted-foreground">
                          <th className="px-5 py-3 font-medium">Model</th>
                          <th className="px-3 py-3 text-right font-medium"><span className="mr-1.5 inline-block h-2 w-2 rounded-full bg-blue-500" />Sinhala</th>
                          <th className="px-3 py-3 text-right font-medium"><span className="mr-1.5 inline-block h-2 w-2 rounded-full bg-emerald-500" />Pali</th>
                          <th className="px-3 py-3 text-right font-medium"><span className="mr-1.5 inline-block h-2 w-2 rounded-full bg-violet-500" />Sanskrit</th>
                          <th className="px-5 py-3 text-right font-medium">Macro</th>
                        </tr>
                      </thead>
                      <tbody className="font-mono tabular-nums">
                        {MODELS.map((m) => (
                          <tr key={m.name} className="border-b last:border-0">
                            <td className="px-5 py-3 font-sans font-medium">{m.name}</td>
                            <td className="px-3 py-3 text-right">{pct(m.sin)}</td>
                            <td className="px-3 py-3 text-right">{pct(m.pli)}</td>
                            <td className="px-3 py-3 text-right">{pct(m.san)}</td>
                            <td className="px-5 py-3 text-right font-semibold text-primary">{pct(m.macro)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                <p className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
                  <X className="h-3.5 w-3.5 text-rose-500" />
                  The same models off the shelf: about 72% on Sinhala, 0% on Pali and Sanskrit.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Audiences */}
        <section className="border-t bg-secondary/30 py-20 sm:py-24">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="mx-auto mb-12 max-w-2xl text-center">
              <Eyebrow>Who it&apos;s for</Eyebrow>
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">Built for the people who work with these texts</h2>
            </div>
            <div className="mx-auto grid max-w-6xl gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { icon: GraduationCap, title: "Scholars & students", body: "Of Buddhist literature, Pali and Sanskrit: find every verse in a commentary." },
                { icon: BookOpen, title: "Monastic libraries", body: "Catalogue collections by language without reading every page." },
                { icon: Landmark, title: "Archives & digitisation", body: "Turn scanned books and journals into language-labelled text." },
                { icon: Database, title: "NLP researchers", body: "Build clean Sinhala, Pali and Sanskrit corpora, sentence by sentence." },
              ].map(({ icon: Icon, title, body }) => (
                <div key={title} className="rounded-2xl border bg-white p-6 shadow-sm transition-all hover:border-primary/30 hover:shadow-md">
                  <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <h3 className="mb-2 font-semibold">{title}</h3>
                  <p className="text-sm leading-relaxed text-muted-foreground">{body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Pricing + dashboard */}
        <section className="py-20 sm:py-28">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-6xl">
              <Feature
                eyebrow="Simple pricing"
                title="Pay only for what you use"
                body="Top up your balance once and spend it as you go. OCR is charged per page and language identification per word, and every charge and refund is listed on your Usage page."
                points={[
                  "Top up in Sri Lankan rupees via PayHere: card, mobile wallet or online banking",
                  "Cancelled work is refunded automatically",
                  "Your dashboard keeps all your texts and documents one click away",
                ]}
              >
                <Screenshot src={dashboard} alt="The LangID dashboard: credit balance, document and classification counts, and recent work." url="LangID · Dashboard" />
              </Feature>
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="px-4 pb-20 sm:px-6 sm:pb-28 lg:px-8">
          <div className="relative mx-auto max-w-6xl overflow-hidden rounded-3xl bg-gradient-to-br from-blue-700 via-blue-600 to-indigo-700 px-6 py-16 text-center text-white shadow-2xl sm:px-12 sm:py-20">
            <div className="absolute inset-0 -z-0 bg-[radial-gradient(ellipse_60%_80%_at_50%_120%,rgba(255,255,255,0.18),transparent)]" />
            <div className="relative">
              <p className={cn("mb-6 text-lg text-blue-100 sm:text-xl", sinhala.className)}>
                <span className="rounded bg-blue-400/30 px-1">සිංහල</span> ·{" "}
                <span className="rounded bg-emerald-400/30 px-1">පාළි</span> ·{" "}
                <span className="rounded bg-violet-400/30 px-1">සංස්කෘත</span>
              </p>
              <h2 className="mx-auto mb-5 max-w-3xl text-3xl font-bold tracking-tight sm:text-5xl">
                Paste a passage. Upload a book. See what&apos;s really on the page.
              </h2>
              <p className="mx-auto mb-10 max-w-xl text-blue-100">
                Create a free account and identify your first text in minutes.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-4">
                <Link href="/auth/signup">
                  <Button size="lg" className="group h-12 bg-white px-8 text-base text-blue-700 shadow-lg hover:bg-blue-50">
                    Create free account
                    <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                  </Button>
                </Link>
                <Link href="/auth/login">
                  <Button size="lg" variant="outline" className="h-12 border-white/40 bg-transparent px-8 text-base text-white hover:bg-white/10 hover:text-white">
                    Log in
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t py-10">
        <div className="container mx-auto flex flex-col items-center justify-between gap-4 px-4 text-xs text-muted-foreground sm:flex-row sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <Logo size={22} labelClassName="text-sm font-semibold" />
            <span>Language identification for Sinhala-script texts</span>
          </div>
          <nav className="flex gap-5">
            <a href="#problem" className="hover:text-foreground">The gap</a>
            <a href="#tour" className="hover:text-foreground">Product tour</a>
            <a href="#research" className="hover:text-foreground">Research</a>
          </nav>
          <p>© {new Date().getFullYear()} LangID. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
