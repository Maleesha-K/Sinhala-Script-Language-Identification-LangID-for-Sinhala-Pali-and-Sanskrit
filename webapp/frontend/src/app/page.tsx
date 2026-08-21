import Link from "next/link";
import { ArrowRight, Globe, ShieldCheck, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col bg-background selection:bg-primary/20 selection:text-primary">
      {/* Navigation */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/80 backdrop-blur-md supports-[backdrop-filter]:bg-background/40">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center gap-2 font-bold text-xl tracking-tight">
              <Globe className="h-6 w-6 text-primary" />
              <span>LangID</span>
            </div>
            <nav className="flex items-center gap-4">
              <Link href="/auth/login">
                <Button variant="ghost" className="hidden sm:flex font-medium">Log In</Button>
              </Link>
              <Link href="/auth/register">
                <Button className="font-medium bg-primary text-primary-foreground shadow-sm hover:bg-primary/90">Sign Up</Button>
              </Link>
            </nav>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative overflow-hidden pt-24 pb-32 sm:pt-32 sm:pb-40 lg:pb-48">
          {/* Background Gradients */}
          <div className="absolute inset-x-0 -top-40 -z-10 transform-gpu overflow-hidden blur-3xl sm:-top-80">
            <div
              className="relative left-[calc(50%-11rem)] aspect-[1155/678] w-[36.125rem] -translate-x-1/2 rotate-[30deg] bg-gradient-to-tr from-[#ff80b5] to-[#9089fc] opacity-20 sm:left-[calc(50%-30rem)] sm:w-[72.1875rem]"
              style={{
                clipPath:
                  "polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)",
              }}
            />
          </div>

          <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative">
            <div className="mx-auto max-w-3xl text-center">
              <div className="mb-8 flex justify-center">
                <div className="relative rounded-full px-3 py-1 text-sm leading-6 text-muted-foreground ring-1 ring-border hover:ring-muted-foreground/30 transition-all cursor-default bg-muted/50 backdrop-blur-sm">
                  Announcing our Next-Gen NLP Classifier.{" "}
                  <a href="#" className="font-semibold text-primary">
                    <span className="absolute inset-0" aria-hidden="true" />
                    Read more <span aria-hidden="true">&rarr;</span>
                  </a>
                </div>
              </div>
              
              <h1 className="text-4xl font-extrabold tracking-tight sm:text-6xl mb-8 bg-clip-text text-transparent bg-gradient-to-b from-foreground to-foreground/70">
                Identify Sinhala, Pali & Sanskrit with Precision
              </h1>
              
              <p className="mt-6 text-lg leading-8 text-muted-foreground mb-10 max-w-2xl mx-auto">
                Upload historical texts, automate transcription workflows, and instantly classify historical South Asian languages using our cutting-edge machine learning models.
              </p>
              
              <div className="flex items-center justify-center gap-x-6">
                <Link href="/dashboard">
                  <Button size="lg" className="h-12 px-8 text-base shadow-lg hover:shadow-xl transition-all duration-300 group">
                    Go to Dashboard
                    <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                  </Button>
                </Link>
                <a href="#features" className="text-sm font-semibold leading-6 text-foreground hover:text-primary transition-colors">
                  Learn more <span aria-hidden="true">→</span>
                </a>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-24 sm:py-32 bg-muted/30 border-y relative">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-2xl lg:text-center mb-16">
              <h2 className="text-base font-semibold leading-7 text-primary">Advanced NLP</h2>
              <p className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">Everything you need to analyze historical texts</p>
            </div>
            
            <div className="mx-auto max-w-2xl lg:max-w-none">
              <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
                
                <div className="flex flex-col bg-card border rounded-2xl p-8 shadow-sm hover:shadow-md transition-shadow">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7">
                    <div className="h-10 w-10 flex items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <Zap className="h-5 w-5" aria-hidden="true" />
                    </div>
                    Instant Processing
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-muted-foreground">
                    <p className="flex-auto">
                      Powered by Celery and Redis, our backend efficiently distributes high-volume classification jobs in real-time.
                    </p>
                  </dd>
                </div>
                
                <div className="flex flex-col bg-card border rounded-2xl p-8 shadow-sm hover:shadow-md transition-shadow">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7">
                    <div className="h-10 w-10 flex items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <Globe className="h-5 w-5" aria-hidden="true" />
                    </div>
                    Sub-Sentence Accuracy
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-muted-foreground">
                    <p className="flex-auto">
                      Choose between full text, paragraph, or sentence-level segmentation to accurately identify mixed-language documents.
                    </p>
                  </dd>
                </div>
                
                <div className="flex flex-col bg-card border rounded-2xl p-8 shadow-sm hover:shadow-md transition-shadow">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7">
                    <div className="h-10 w-10 flex items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <ShieldCheck className="h-5 w-5" aria-hidden="true" />
                    </div>
                    Community Driven
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-muted-foreground">
                    <p className="flex-auto">
                      Help fine-tune our models. Spot a mistake? Report it directly in the dashboard, and our admins will use it to improve future iterations.
                    </p>
                  </dd>
                </div>
                
              </dl>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t bg-card py-12">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-muted-foreground">
          <div className="flex justify-center gap-2 items-center mb-4">
            <Globe className="h-5 w-5" />
            <span className="font-semibold text-foreground tracking-tight">LangID Platform</span>
          </div>
          <p>© {new Date().getFullYear()} LangID. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
