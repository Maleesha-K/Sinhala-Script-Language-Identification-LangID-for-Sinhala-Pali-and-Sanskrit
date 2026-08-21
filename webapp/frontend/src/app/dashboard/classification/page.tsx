"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { toast } from "sonner";
import { Loader2, Activity } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

export default function ClassificationPage() {
  const router = useRouter();
  const [text, setText] = useState("");
  const [strategy, setStrategy] = useState("sentence");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) {
      toast.error("Please enter some text to classify");
      return;
    }

    setLoading(true);
    try {
      const res = await axios.post("/api/classification/jobs", {
        input_text: text,
        segmentation_strategy: strategy
      });
      toast.success("Classification job started!");
      router.push(`/dashboard/classification/${res.data.id}`);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to start classification");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Language Identification</h1>
        <p className="text-muted-foreground mt-2">
          Paste text in Sinhala, Pali, or Sanskrit to identify its language.
        </p>
      </div>

      <div className="bg-card border rounded-lg p-6 shadow-sm">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="text-input" className="text-base font-semibold">
              Input Text
            </Label>
            <Textarea
              id="text-input"
              placeholder="Paste your text here..."
              className="min-h-[250px] resize-y p-4 text-base"
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
          </div>

          <div className="space-y-3">
            <Label className="text-base font-semibold">Segmentation Strategy</Label>
            <p className="text-sm text-muted-foreground">
              How should we split the text before analyzing it?
            </p>
            <RadioGroup value={strategy} onValueChange={setStrategy} className="grid sm:grid-cols-3 gap-4 pt-2">
              <div>
                <RadioGroupItem value="sentence" id="sentence" className="peer sr-only" />
                <Label
                  htmlFor="sentence"
                  className="flex flex-col items-center justify-between rounded-md border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary [&:has([data-state=checked])]:border-primary cursor-pointer transition-all"
                >
                  <span className="font-semibold mb-1">Sentence</span>
                  <span className="text-xs text-center text-muted-foreground">Splits text by typical punctuation.</span>
                </Label>
              </div>
              <div>
                <RadioGroupItem value="paragraph" id="paragraph" className="peer sr-only" />
                <Label
                  htmlFor="paragraph"
                  className="flex flex-col items-center justify-between rounded-md border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary [&:has([data-state=checked])]:border-primary cursor-pointer transition-all"
                >
                  <span className="font-semibold mb-1">Paragraph</span>
                  <span className="text-xs text-center text-muted-foreground">Splits text by newlines.</span>
                </Label>
              </div>
              <div>
                <RadioGroupItem value="full_text" id="full_text" className="peer sr-only" />
                <Label
                  htmlFor="full_text"
                  className="flex flex-col items-center justify-between rounded-md border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary [&:has([data-state=checked])]:border-primary cursor-pointer transition-all"
                >
                  <span className="font-semibold mb-1">Full Text</span>
                  <span className="text-xs text-center text-muted-foreground">Analyzes everything as a single block.</span>
                </Label>
              </div>
            </RadioGroup>
          </div>

          <div className="pt-4 flex justify-end">
            <Button type="submit" size="lg" disabled={loading} className="w-full sm:w-auto">
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Activity className="mr-2 h-4 w-4" />
                  Identify Language
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
