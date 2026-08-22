"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { toast } from "sonner";
import { Loader2, Plus, CheckCircle2, XCircle, Boxes } from "lucide-react";
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageHeader } from "@/components/layout/page-header";
import { cn } from "@/lib/utils";

type Tier = {
  id: string;
  name: string;
  price_usd: number;
  included_credits: number;
  ocr_pages_included: number;
  is_active: boolean;
};

export default function TiersPage() {
  const [tiers, setTiers] = useState<Tier[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);

  const [formData, setFormData] = useState({
    name: "", price_usd: 0, included_credits: 0, ocr_pages_included: 0,
  });

  useEffect(() => { fetchTiers(); }, []);

  const fetchTiers = async () => {
    try {
      const res = await axios.get("/api/admin/tiers");
      setTiers(res.data);
    } catch { toast.error("Failed to load tiers"); }
    finally { setLoading(false); }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await axios.post("/api/admin/tiers", formData);
      toast.success("Tier created");
      setOpen(false);
      fetchTiers();
      setFormData({ name: "", price_usd: 0, included_credits: 0, ocr_pages_included: 0 });
    } catch { toast.error("Failed to create tier"); }
    finally { setCreating(false); }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tiers Management"
        description="Define subscription plans with pricing, credits, and OCR limits."
        actions={
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger
              render={
                <Button size="sm" className="gap-2">
                  <Plus className="h-4 w-4" />
                  Add Tier
                </Button>
              }
            />
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Tier</DialogTitle>
                <DialogDescription>Define a subscription tier with its pricing and limits.</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleCreate} className="space-y-4 pt-2">
                <div className="space-y-1.5">
                  <Label htmlFor="name">Tier Name</Label>
                  <Input id="name" required value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} placeholder="e.g. Pro Plan" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="price">Monthly Price (USD)</Label>
                    <Input id="price" type="number" step="0.01" required value={formData.price_usd} onChange={(e) => setFormData({ ...formData, price_usd: parseFloat(e.target.value) })} />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="credits">Included Credits</Label>
                    <Input id="credits" type="number" required value={formData.included_credits} onChange={(e) => setFormData({ ...formData, included_credits: parseFloat(e.target.value) })} />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="ocr">OCR Pages Included</Label>
                  <Input id="ocr" type="number" required value={formData.ocr_pages_included} onChange={(e) => setFormData({ ...formData, ocr_pages_included: parseInt(e.target.value) })} />
                </div>
                <Button type="submit" className="w-full" disabled={creating}>
                  {creating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                  Create Tier
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        }
      />

      <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/40 hover:bg-muted/40">
              <TableHead className="font-semibold">Name</TableHead>
              <TableHead className="font-semibold">Price</TableHead>
              <TableHead className="font-semibold">Credits</TableHead>
              <TableHead className="font-semibold">OCR Pages</TableHead>
              <TableHead className="font-semibold">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow><TableCell colSpan={5} className="h-36 text-center"><Loader2 className="h-6 w-6 animate-spin mx-auto text-primary" /></TableCell></TableRow>
            ) : tiers.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="h-36 text-center">
                  <div className="flex flex-col items-center gap-3 text-muted-foreground">
                    <Boxes className="h-8 w-8 opacity-40" />
                    <p className="text-sm">No tiers yet. Create one to get started.</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              tiers.map((tier) => (
                <TableRow key={tier.id} className="hover:bg-muted/30">
                  <TableCell className="font-medium">{tier.name}</TableCell>
                  <TableCell className="text-sm">${tier.price_usd.toFixed(2)}</TableCell>
                  <TableCell className="text-sm">{tier.included_credits.toLocaleString()}</TableCell>
                  <TableCell className="text-sm">{tier.ocr_pages_included.toLocaleString()}</TableCell>
                  <TableCell>
                    <span className={cn(
                      "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium border",
                      tier.is_active
                        ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                        : "bg-muted text-muted-foreground border-border"
                    )}>
                      {tier.is_active
                        ? <><CheckCircle2 className="h-3 w-3" />Active</>
                        : <><XCircle className="h-3 w-3" />Inactive</>
                      }
                    </span>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
