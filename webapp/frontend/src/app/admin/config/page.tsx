"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Loader2, Settings, DollarSign } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";

export default function SystemConfigPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [rate, setRate] = useState("100.0");

  useEffect(() => { fetchConfig(); }, []);

  const fetchConfig = async () => {
    try {
      const res = await axios.get("/api/admin/config");
      setRate(res.data.usd_to_credits_rate?.toString() ?? "100");
    } catch { toast.error("Failed to load configuration"); }
    finally { setLoading(false); }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.put("/api/admin/config", { usd_to_credits_rate: parseFloat(rate) });
      toast.success("Configuration saved");
    } catch { toast.error("Failed to save configuration"); }
    finally { setSaving(false); }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="System Configuration"
        description="Manage global platform settings and conversion rates."
      />

      <div className="grid gap-6 md:grid-cols-2">
        {/* Exchange rate card */}
        <div className="rounded-xl border border-border bg-white shadow-sm p-6 space-y-5">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-primary/10 flex items-center justify-center">
              <DollarSign className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h3 className="text-sm font-semibold">Exchange Rate</h3>
              <p className="text-xs text-muted-foreground">Credits awarded per $1 USD</p>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="rate" className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              USD → Credits Rate
            </Label>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground font-medium min-w-[24px]">$1</span>
              <span className="text-muted-foreground">=</span>
              <Input
                id="rate"
                type="number"
                step="0.1"
                min="0"
                value={rate}
                onChange={(e) => setRate(e.target.value)}
                className="w-32"
              />
              <span className="text-sm text-muted-foreground font-medium">credits</span>
            </div>
          </div>

          <Button onClick={handleSave} disabled={saving} size="sm" className="gap-2">
            {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Settings className="h-3.5 w-3.5" />}
            Save Changes
          </Button>
        </div>
      </div>
    </div>
  );
}
