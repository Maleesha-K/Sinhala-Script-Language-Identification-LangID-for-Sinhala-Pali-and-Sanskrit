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
  Settings, 
  DollarSign, 
  Coins, 
  Package, 
  Sparkles, 
  RefreshCw,
  CheckCircle2
} from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";

interface CreditPackageConfig {
  id: string;
  name: string;
  credits: number;
  amount_lkr: number;
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
      if (data.packages && Array.isArray(data.packages)) {
        setPackages(data.packages);
      } else {
        // Fallback default packages scaled with rate
        recalculatePackagesFromRate(parseFloat(data.usd_to_credits_rate || "100"));
      }
    } catch { 
      toast.error("Failed to load system configuration"); 
    } finally { 
      setLoading(false); 
    }
  };

  const recalculatePackagesFromRate = (creditsPerUsd: number) => {
    const r = creditsPerUsd > 0 ? creditsPerUsd : 100.0;
    setPackages([
      {
        id: "starter",
        name: "Student / Starter Pack",
        credits: Math.round(25.0 * r),
        amount_lkr: 750.00,
        popular: false,
        description: "Ideal for students and short document experiments."
      },
      {
        id: "standard",
        name: "Standard Researcher Pack",
        credits: Math.round(100.0 * r),
        amount_lkr: 2500.00,
        popular: true,
        description: "Best value for continuous classification and multi-page OCR."
      },
      {
        id: "institution",
        name: "Institutional / Corpus Pack",
        credits: Math.round(500.0 * r),
        amount_lkr: 10000.00,
        popular: false,
        description: "High-volume tier for large historical archives and deep datasets."
      }
    ]);
  };

  const handlePackageChange = (index: number, field: "credits" | "amount_lkr" | "name", value: any) => {
    const updated = [...packages];
    updated[index] = {
      ...updated[index],
      [field]: field === "name" ? value : Math.max(0, parseFloat(value) || 0)
    };
    setPackages(updated);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {
        usd_to_credits_rate: parseFloat(rate) || 100.0,
        usd_to_lkr_rate: parseFloat(lkrRate) || 300.0,
        packages: packages
      };

      await axios.put("/api/admin/config", payload);
      toast.success("System configuration and credit top-up packages saved successfully!");
    } catch { 
      toast.error("Failed to save configuration"); 
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

  const effectiveRateLkr = (parseFloat(lkrRate) || 300) / (parseFloat(rate) || 100);

  return (
    <div className="space-y-6">
      <PageHeader
        title="System Configuration"
        description="Manage global credit issuing rates, USD/LKR exchange conversions, and user top-up packages."
      />

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column: Global Exchange Rates */}
        <div className="space-y-6 lg:col-span-1">
          <div className="rounded-xl border border-border bg-white shadow-sm p-6 space-y-5">
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-lg bg-primary/10 flex items-center justify-center">
                <DollarSign className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h3 className="text-sm font-semibold">USD → Credits Rate</h3>
                <p className="text-xs text-muted-foreground">Base credit issuance multiplier</p>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="rate" className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                Credits Awarded per $1 USD
              </Label>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground font-medium min-w-[24px]">$1</span>
                <span className="text-muted-foreground">=</span>
                <Input
                  id="rate"
                  type="number"
                  step="1"
                  min="1"
                  value={rate}
                  onChange={(e) => {
                    const newRate = e.target.value;
                    setRate(newRate);
                  }}
                  className="w-32"
                />
                <span className="text-sm text-muted-foreground font-medium">credits</span>
              </div>
            </div>

            <div className="space-y-2 pt-2 border-t border-slate-100">
              <Label htmlFor="lkrRate" className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                USD → LKR Conversion Rate
              </Label>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground font-medium min-w-[24px]">$1</span>
                <span className="text-muted-foreground">=</span>
                <Input
                  id="lkrRate"
                  type="number"
                  step="1"
                  min="1"
                  value={lkrRate}
                  onChange={(e) => setLkrRate(e.target.value)}
                  className="w-32"
                />
                <span className="text-sm text-muted-foreground font-medium">LKR</span>
              </div>
            </div>

            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/80 text-xs space-y-1">
              <div className="flex justify-between text-muted-foreground">
                <span>Effective Unit Price:</span>
                <span className="font-semibold text-foreground">
                  ~LKR {effectiveRateLkr.toFixed(2)} / credit
                </span>
              </div>
            </div>

            <Button 
              type="button" 
              variant="outline" 
              size="sm" 
              onClick={() => recalculatePackagesFromRate(parseFloat(rate))}
              className="w-full text-xs gap-1.5"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Recalculate Packages from Rate
            </Button>
          </div>
        </div>

        {/* Right Column: User Buying Packages Configuration */}
        <div className="space-y-6 lg:col-span-2">
          <div className="rounded-xl border border-border bg-white shadow-sm p-6 space-y-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                  <Package className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold">User Top-Up Packages</h3>
                  <p className="text-xs text-muted-foreground">
                    Customize the token amount and LKR price presented to users on the &quot;Top Up Credits&quot; modal.
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              {packages.map((pkg, idx) => (
                <div 
                  key={pkg.id} 
                  className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                        Tier {idx + 1}:
                      </span>
                      <Input
                        value={pkg.name}
                        onChange={(e) => handlePackageChange(idx, "name", e.target.value)}
                        className="h-8 text-xs font-semibold bg-white w-56"
                      />
                    </div>
                    {pkg.popular && (
                      <Badge className="bg-primary text-white text-[10px]">
                        <Sparkles className="h-3 w-3 mr-1" /> Most Popular
                      </Badge>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-xs text-muted-foreground">Issued Credits</Label>
                      <div className="relative mt-1">
                        <Input
                          type="number"
                          step="100"
                          min="100"
                          value={pkg.credits}
                          onChange={(e) => handlePackageChange(idx, "credits", e.target.value)}
                          className="h-9 bg-white font-bold text-foreground pl-8"
                        />
                        <Coins className="h-4 w-4 text-primary absolute left-2.5 top-1/2 -translate-y-1/2" />
                      </div>
                    </div>

                    <div>
                      <Label className="text-xs text-muted-foreground">Price in LKR</Label>
                      <div className="relative mt-1">
                        <Input
                          type="number"
                          step="50"
                          min="10"
                          value={pkg.amount_lkr}
                          onChange={(e) => handlePackageChange(idx, "amount_lkr", e.target.value)}
                          className="h-9 bg-white font-bold text-primary pl-12"
                        />
                        <span className="text-xs font-bold text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2">
                          LKR
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="pt-2 flex justify-end">
              <Button onClick={handleSave} disabled={saving} className="gap-2 px-6">
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
      </div>
    </div>
  );
}
