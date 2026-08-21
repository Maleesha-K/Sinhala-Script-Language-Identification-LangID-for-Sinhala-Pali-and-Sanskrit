"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { toast } from "sonner";
import { Loader2, Plus } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

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
    name: "",
    price_usd: 0,
    included_credits: 0,
    ocr_pages_included: 0,
  });

  useEffect(() => {
    fetchTiers();
  }, []);

  const fetchTiers = async () => {
    try {
      const res = await axios.get("/api/admin/tiers");
      setTiers(res.data);
    } catch (error) {
      toast.error("Failed to load tiers");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await axios.post("/api/admin/tiers", formData);
      toast.success("Tier created successfully");
      setOpen(false);
      fetchTiers();
      setFormData({ name: "", price_usd: 0, included_credits: 0, ocr_pages_included: 0 });
    } catch (error) {
      toast.error("Failed to create tier");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Tiers Management</h1>
          <p className="text-muted-foreground mt-2">
            Create and manage subscription tiers.
          </p>
        </div>
        
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Add Tier
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Tier</DialogTitle>
              <DialogDescription>
                Define a new subscription tier with its pricing and limits.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Tier Name</Label>
                <Input 
                  id="name" 
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="e.g. Pro Plan"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="price">Monthly Price (USD)</Label>
                <Input 
                  id="price" 
                  type="number"
                  step="0.01"
                  required
                  value={formData.price_usd}
                  onChange={(e) => setFormData({...formData, price_usd: parseFloat(e.target.value)})}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="credits">Included Credits</Label>
                <Input 
                  id="credits" 
                  type="number"
                  required
                  value={formData.included_credits}
                  onChange={(e) => setFormData({...formData, included_credits: parseFloat(e.target.value)})}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ocr">OCR Pages Included</Label>
                <Input 
                  id="ocr" 
                  type="number"
                  required
                  value={formData.ocr_pages_included}
                  onChange={(e) => setFormData({...formData, ocr_pages_included: parseInt(e.target.value)})}
                />
              </div>
              <Button type="submit" className="w-full" disabled={creating}>
                {creating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                Create Tier
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="border rounded-md">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Price (USD)</TableHead>
              <TableHead>Included Credits</TableHead>
              <TableHead>OCR Pages</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={5} className="h-24 text-center">
                  <Loader2 className="h-6 w-6 animate-spin mx-auto text-muted-foreground" />
                </TableCell>
              </TableRow>
            ) : tiers.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                  No tiers found. Create one to get started.
                </TableCell>
              </TableRow>
            ) : (
              tiers.map((tier) => (
                <TableRow key={tier.id}>
                  <TableCell className="font-medium">{tier.name}</TableCell>
                  <TableCell>${tier.price_usd}</TableCell>
                  <TableCell>{tier.included_credits}</TableCell>
                  <TableCell>{tier.ocr_pages_included}</TableCell>
                  <TableCell>{tier.is_active ? "Active" : "Inactive"}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
