import Link from "next/link";
import { ArrowRight, Globe, ShieldCheck, Zap, BookOpen, BarChart2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AppHeader } from "@/components/layout/app-header";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col bg-white">
      <AppHeader />

      <main className="flex-1">
        {/* Hero */}
        <section className="relative overflow-hidden py-24 sm:py-32">
          {/* Subtle blue gradient background */}
          <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(59,130,246,0.12),transparent)]" />

          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-3xl text-center">
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-sm text-primary font-medium mb-8">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                </span>
                ML-Powered Language Identification
              </div>

              <h1 className="text-4xl font-extrabold tracking-tight sm:text-6xl text-foreground mb-6">
                Identify{" "}
                <span className="text-primary">Sinhala</span>,{" "}
                <span className="text-primary">Pali</span> &{" "}
                <span className="text-primary">Sanskrit</span>
              </h1>

              <p className="text-lg text-muted-foreground mb-10 max-w-2xl mx-auto leading-relaxed">
                Upload historical manuscripts or paste raw text. Our ML model identifies South Asian languages at the sentence level with high confidence scores.
              </p>

              <div className="flex flex-wrap items-center justify-center gap-4">
                <Link href="/dashboard">
                  <Button size="lg" className="h-11 px-8 shadow-md hover:shadow-lg transition-shadow group">
                    Go to Dashboard
                    <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
                  </Button>
                </Link>
                <Link href="/auth/register">
                  <Button size="lg" variant="outline" className="h-11 px-8 border-primary/30 text-primary hover:bg-primary/5">
                    Create Free Account
                  </Button>
                </Link>
              </div>
            </div>

            {/* Trust strip */}
            <div className="mt-16 flex flex-wrap items-center justify-center gap-8 text-xs text-muted-foreground font-medium uppercase tracking-wider">
              <span className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-primary" />Secure by design</span>
              <span className="flex items-center gap-2"><Zap className="h-4 w-4 text-primary" />Real-time results</span>
              <span className="flex items-center gap-2"><BookOpen className="h-4 w-4 text-primary" />Community annotations</span>
              <span className="flex items-center gap-2"><BarChart2 className="h-4 w-4 text-primary" />Confidence scores</span>
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="py-20 border-t bg-secondary/30">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-14">
              <h2 className="text-2xl font-bold tracking-tight mb-3">Built for Scholars & Researchers</h2>
              <p className="text-muted-foreground max-w-xl mx-auto text-sm">
                Every feature is designed around the challenges of working with historical South Asian language texts.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
              {[
                {
                  icon: Zap,
                  title: "Sub-Sentence Accuracy",
                  desc: "Classify at sentence, paragraph, or full-text granularity. Mixed-language documents are handled correctly.",
                },
                {
                  icon: Globe,
                  title: "Document Pipeline",
                  desc: "Upload PDFs, run OCR, and send extracted text straight to language identification — all in one workflow.",
                },
                {
                  icon: ShieldCheck,
                  title: "Annotation & Feedback",
                  desc: "Spot a mistake? Report it. Admin-reviewed corrections become future training data to improve the model.",
                },
              ].map(({ icon: Icon, title, desc }) => (
                <div key={title} className="bg-white rounded-xl border border-border p-6 shadow-sm hover:shadow-md hover:border-primary/30 transition-all">
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <h3 className="font-semibold text-sm mb-2">{title}</h3>
                  <p className="text-muted-foreground text-sm leading-relaxed">{desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t py-8">
        <div className="container mx-auto px-4 text-center text-xs text-muted-foreground">
          <div className="flex justify-center items-center gap-2 mb-2">
            <Globe className="h-4 w-4 text-primary" />
            <span className="font-semibold text-foreground">LangID Platform</span>
          </div>
          <p>© {new Date().getFullYear()} LangID. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
