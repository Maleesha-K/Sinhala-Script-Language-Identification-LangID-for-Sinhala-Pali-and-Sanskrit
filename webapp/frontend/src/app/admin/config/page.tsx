"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

export default function SystemConfigPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [rate, setRate] = useState("100.0");

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await axios.get("/api/admin/config");
      setRate(res.data.usd_to_credits_rate.toString());
    } catch (error) {
      toast.error("Failed to load configuration");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.put("/api/admin/config", {
        usd_to_credits_rate: parseFloat(rate)
      });
      toast.success("Configuration updated successfully");
    } catch (error) {
      toast.error("Failed to update configuration");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">System Configuration</h1>
        <p className="text-muted-foreground mt-2">
          Manage global platform settings and exchange rates.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Exchange Rates</CardTitle>
            <CardDescription>
              Configure how many credits a user receives for $1 USD.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="rate">USD to Credits Rate</Label>
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">$1 = </span>
                <Input 
                  id="rate" 
                  type="number" 
                  value={rate}
                  onChange={(e) => setRate(e.target.value)}
                  step="0.1"
                />
                <span className="text-muted-foreground">credits</span>
              </div>
            </div>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Save Configuration
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
