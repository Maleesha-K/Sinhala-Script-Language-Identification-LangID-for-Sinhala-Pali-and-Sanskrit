"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { PageHeader } from "@/components/layout/page-header";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus, Edit2, Loader2, Trash2 } from "lucide-react";

interface ModelRate {
  id: string;
  model_type: "classification" | "ocr";
  model_name: string;
  credits_per_token: number;
  credits_per_page: number;
  is_active: boolean;
}

interface AvailableModel {
  model_name: string;
  model_type: string;
  description: string;
}

export default function AdminRatesPage() {
  const [rates, setRates] = useState<ModelRate[]>([]);
  const [availableModels, setAvailableModels] = useState<AvailableModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingRate, setEditingRate] = useState<ModelRate | null>(null);

  const [formData, setFormData] = useState({
    model_type: "classification",
    model_name: "",
    credits_per_token: "0",
    credits_per_page: "0",
    is_active: true
  });

  const fetchData = async () => {
    try {
      setLoading(true);
      const [ratesRes, modelsRes] = await Promise.all([
        axios.get("/api/admin/rates"),
        axios.get("/api/admin/rates/available-models")
      ]);
      setRates(ratesRes.data.data || []);
      setAvailableModels(modelsRes.data.data || []);
    } catch (error) {
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOpenDialog = (rate?: ModelRate) => {
    if (rate) {
      setEditingRate(rate);
      setFormData({
        model_type: rate.model_type,
        model_name: rate.model_name,
        credits_per_token: rate.credits_per_token.toString(),
        credits_per_page: rate.credits_per_page.toString(),
        is_active: rate.is_active
      });
    } else {
      setEditingRate(null);
      setFormData({
        model_type: "classification",
        model_name: "",
        credits_per_token: "0",
        credits_per_page: "0",
        is_active: true
      });
    }
    setIsDialogOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.model_name) {
      toast.error("Please select a model");
      return;
    }
    try {
      const payload = {
        model_type: formData.model_type,
        model_name: formData.model_name,
        credits_per_token: parseFloat(formData.credits_per_token) || 0,
        credits_per_page: parseFloat(formData.credits_per_page) || 0,
        is_active: formData.is_active
      };

      if (editingRate) {
        await axios.put(`/api/admin/rates/${editingRate.id}`, payload);
        toast.success("Rate updated");
      } else {
        await axios.post("/api/admin/rates", payload);
        toast.success("Rate created");
      }
      setIsDialogOpen(false);
      fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.error || "Failed to save rate");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this rate?")) return;
    try {
      await axios.delete(`/api/admin/rates/${id}`);
      toast.success("Rate deleted");
      fetchData();
    } catch (error) {
      toast.error("Failed to delete rate");
    }
  };

  // Filter available models for the dropdown based on selected model_type
  const filteredModels = availableModels.filter(m => m.model_type === formData.model_type);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <PageHeader title="Model Rates" description="Manage cost assignments for OCR and Classification models." />
        <Button onClick={() => handleOpenDialog()} className="gap-2">
          <Plus className="h-4 w-4" /> Add Rate
        </Button>
      </div>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingRate ? "Edit Rate" : "Add New Rate"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label>Model Type</Label>
              <Select 
                value={formData.model_type} 
                onValueChange={(val) => {
                  setFormData({...formData, model_type: val, model_name: ""});
                }}
                disabled={!!editingRate}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="classification">Classification (LangID)</SelectItem>
                  <SelectItem value="ocr">OCR</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Model Name</Label>
              {editingRate ? (
                <Input 
                  value={formData.model_name} 
                  disabled
                />
              ) : (
                <Select 
                  value={formData.model_name} 
                  onValueChange={(val) => setFormData({...formData, model_name: val})}
                >
                  <SelectTrigger><SelectValue placeholder="Select a model..." /></SelectTrigger>
                  <SelectContent>
                    {filteredModels.map((m) => (
                      <SelectItem key={m.model_name} value={m.model_name}>
                        {m.model_name} <span className="text-muted-foreground text-xs ml-2">({m.description})</span>
                      </SelectItem>
                    ))}
                    {filteredModels.length === 0 && (
                      <SelectItem value="none" disabled>No models available for this type</SelectItem>
                    )}
                  </SelectContent>
                </Select>
              )}
            </div>
            
            {formData.model_type === "classification" && (
              <div className="space-y-2">
                <Label>Credits Per Token</Label>
                <Input 
                  type="number" 
                  step="0.0001"
                  value={formData.credits_per_token} 
                  onChange={(e) => setFormData({...formData, credits_per_token: e.target.value})}
                  required
                />
              </div>
            )}
            
            {formData.model_type === "ocr" && (
              <div className="space-y-2">
                <Label>Credits Per Page</Label>
                <Input 
                  type="number" 
                  step="0.01"
                  value={formData.credits_per_page} 
                  onChange={(e) => setFormData({...formData, credits_per_page: e.target.value})}
                  required
                />
              </div>
            )}

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
              <Button type="submit">Save</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 flex justify-center"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Model Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Cost</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rates.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                    No rates found. System will auto-create defaults on first run.
                  </TableCell>
                </TableRow>
              ) : (
                rates.map((rate) => (
                  <TableRow key={rate.id}>
                    <TableCell className="font-medium">{rate.model_name}</TableCell>
                    <TableCell className="capitalize">{rate.model_type}</TableCell>
                    <TableCell>
                      {rate.model_type === "classification" 
                        ? `${rate.credits_per_token} / token`
                        : `${rate.credits_per_page} / page`}
                    </TableCell>
                    <TableCell>
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${rate.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
                        {rate.is_active ? "Active" : "Inactive"}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="icon" onClick={() => handleOpenDialog(rate)}>
                        <Edit2 className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" className="text-destructive hover:text-destructive/90" onClick={() => handleDelete(rate.id)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
}
