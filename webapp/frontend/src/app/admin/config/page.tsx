"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { 
  Loader2, 
  Coins, 
  Package, 
  Sparkles, 
  CheckCircle2
} from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";

interface CreditPackageConfig {
  id: string;
  name: string;
  credits: number | string;
  amount_lkr: number | string;
  popular: boolean;
  description: string;
}

export default function SystemConfigPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [rate, setRate] = useState("100.0");
  const [lkrRate, setLkrRate] = useState("300.0");
  const [packages, setPackages] = useState<CreditPackageConfig[]>([]);

  useEffect(() => { 
    fetchConfig(); 
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await axios.get("/api/admin/config");
      const data = res.data;
      setRate(data.usd_to_credits_rate?.toString() ?? "100.0");
      setLkrRate(data.usd_to_lkr_rate?.toString() ?? "300.0");
      if (data.packages && Array.isArray(data.packages) && data.packages.length > 0) {
        setPackages(data.packages);
      } else {
        // Fallback default packages
        setPackages([
          {
            id: "starter",
            name: "Student / Starter Pack",
            credits: 7500,
            amount_lkr: 750.00,
            popular: false,
            description: "Ideal for students and short document experiments."
          },
          {
            id: "standard",
            name: "Standard Researcher Pack",
            credits: 30000,
            amount_lkr: 2500.00,
            popular: true,
            description: "Best value for continuous classification and multi-page OCR."
          },
          {
            id: "institution",
            name: "Institutional / Corpus Pack",
            credits: 150000,
            amount_lkr: 10000.00,
            popular: false,
            description: "High-volume tier for large historical archives and deep datasets."
          }
        ]);
      }
    } catch { 
      toast.error("Failed to load credit packages configuration"); 
    } finally { 
      setLoading(false); 
    }
  };

  const handlePackageChange = (
    index: number, 
    field: "credits" | "amount_lkr" | "name", 
    value: string
  ) => {
    const updated = [...packages];
    if (field === "name") {
      updated[index] = {
        ...updated[index],
        name: value
      };
    } else {
      // Allow user to completely erase the field (value === "") without forcing it back to 0
      if (value === "") {
        updated[index] = {
          ...updated[index],
          [field]: ""
        };
      } else {
        // Strip unwanted leading zeros when typing after 0 (e.g., "054545" -> "54545")
        let sanitized = value;
        if (/^0[0-9]/.test(sanitized)) {
          sanitized = sanitized.replace(/^0+/, "") || "0";
        }
        updated[index] = {
          ...updated[index],
          [field]: sanitized
        };
      }
    }
    setPackages(updated);
  };

  const handleBlur = (index: number, field: "credits" | "amount_lkr") => {
    const updated = [...packages];
    const val = updated[index][field];
    if (val === "" || isNaN(Number(val)) || Number(val) < 0) {
      // Sensible default if left blank
      const fallback = field === "credits" ? 1000 : 100;
      updated[index] = {
        ...updated[index],
        [field]: fallback
      };
      setPackages(updated);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // Ensure all fields are formatted numbers for backend validation
      const sanitizedPackages = packages.map((pkg) => ({
        ...pkg,
        credits: Math.max(0, Number(pkg.credits) || 0),
        amount_lkr: Math.max(0, Number(pkg.amount_lkr) || 0)
      }));

      const payload = {
        usd_to_credits_rate: parseFloat(rate) || 100.0,
        usd_to_lkr_rate: parseFloat(lkrRate) || 300.0,
        packages: sanitizedPackages
      };

      await axios.put("/api/admin/config", payload);
      setPackages(sanitizedPackages);
      toast.success("Credit packages saved successfully!");
    } catch { 
      toast.error("Failed to save packages configuration"); 
    } finally { 
      setSaving(false); 
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <PageHeader
        title="Credit Packages Configuration"
        description="Customize the token amount and LKR prices for the 3 user top-up packages."
      />

      <div className="rounded-xl border border-border bg-white shadow-sm p-6 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100">
              <Package className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-900">User Top-Up Packages</h3>
              <p className="text-xs text-muted-foreground">
                Set individual credit amounts and LKR prices presented to users on the &quot;Top Up Credits&quot; modal.
              </p>
            </div>
          </div>
          <Badge variant="outline" className="text-xs font-medium text-slate-600 bg-slate-50 border-slate-200">
            3 Active Tiers
          </Badge>
        </div>

        <div className="space-y-4">
          {packages.map((pkg, idx) => {
            const creditsNum = Number(pkg.credits) || 0;
            const amountNum = Number(pkg.amount_lkr) || 0;
            const unitPrice = creditsNum > 0 ? (amountNum / creditsNum).toFixed(3) : "0.000";

            return (
              <div 
                key={pkg.id} 
                className="p-5 rounded-xl border border-slate-200/90 bg-slate-50/60 hover:bg-slate-50/90 transition-colors space-y-4 shadow-sm"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-700 uppercase tracking-wider bg-white px-2.5 py-1 rounded-md border border-slate-200">
                      Tier {idx + 1}
                    </span>
                    <Input
                      value={pkg.name}
                      onChange={(e) => handlePackageChange(idx, "name", e.target.value)}
                      placeholder="Package name"
                      className="h-9 text-xs font-semibold bg-white w-64 border-slate-200 shadow-sm"
                    />
                  </div>
                  {pkg.popular && (
                    <Badge className="bg-blue-600 hover:bg-blue-600 text-white text-[11px] self-start sm:self-auto py-0.5 px-2.5 shadow-sm">
                      <Sparkles className="h-3 w-3 mr-1" /> Most Popular
                    </Badge>
                  )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs font-medium text-slate-600">Issued Credits</Label>
                    <div className="relative mt-1.5">
                      <Input
                        type="number"
                        min="0"
                        step="100"
                        value={pkg.credits}
                        onChange={(e) => handlePackageChange(idx, "credits", e.target.value)}
                        onBlur={() => handleBlur(idx, "credits")}
                        placeholder="e.g. 5000"
                        className="h-10 bg-white font-semibold text-slate-900 pl-9 border-slate-200 shadow-sm"
                      />
                      <Coins className="h-4 w-4 text-emerald-600 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                    </div>
                  </div>

                  <div>
                    <Label className="text-xs font-medium text-slate-600">Price in LKR</Label>
                    <div className="relative mt-1.5">
                      <Input
                        type="number"
                        min="0"
                        step="50"
                        value={pkg.amount_lkr}
                        onChange={(e) => handlePackageChange(idx, "amount_lkr", e.target.value)}
                        onBlur={() => handleBlur(idx, "amount_lkr")}
                        placeholder="e.g. 1500"
                        className="h-10 bg-white font-bold text-blue-700 pl-14 border-slate-200 shadow-sm"
                      />
                      <span className="text-xs font-bold text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
                        LKR
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-200/60">
                  <span>Effective Unit Rate:</span>
                  <span className="font-semibold text-slate-700 font-mono">
                    ~LKR {unitPrice} / credit
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        <div className="pt-3 border-t border-slate-100 flex justify-end">
          <Button 
            onClick={handleSave} 
            disabled={saving} 
            className="gap-2 px-6 bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-sm"
          >
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Saving Changes...
              </>
            ) : (
              <>
                <CheckCircle2 className="h-4 w-4" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
