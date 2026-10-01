"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import Script from "next/script";
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogDescription,
  DialogFooter 
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Loader2, Coins, Check, ShieldCheck, Sparkles, CreditCard } from "lucide-react";

interface CreditPackage {
  id: string;
  name: string;
  credits: number;
  amount_lkr: number;
  popular: boolean;
  description: string;
}

interface TopUpModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function TopUpModal({ open, onOpenChange, onSuccess }: TopUpModalProps) {
  const [packages, setPackages] = useState<CreditPackage[]>([]);
  const [selectedId, setSelectedId] = useState<string>("standard");
  const [customCredits, setCustomCredits] = useState<number>(5000);
  const [loading, setLoading] = useState(false);
  const [fetchingPackages, setFetchingPackages] = useState(true);
  const [payhereReady, setPayhereReady] = useState(false);

  useEffect(() => {
    if (!open) return;

    const fetchPackages = async () => {
      try {
        setFetchingPackages(true);
        const res = await axios.get("/api/payments/packages");
        if (res.data?.data) {
          setPackages(res.data.data);
        }
      } catch (err) {
        toast.error("Failed to load credit packages.");
      } finally {
        setFetchingPackages(false);
      }
    };

    fetchPackages();
  }, [open]);

  // Check if PayHere is already loaded in window
  useEffect(() => {
    if (typeof window !== "undefined" && (window as any).payhere) {
      setPayhereReady(true);
    }
  }, []);

  const getActiveAmount = (): { credits: number; amountLkr: number; name: string } => {
    if (selectedId === "custom") {
      const credits = Math.max(1000, Number(customCredits) || 1000);
      const amountLkr = Math.round(credits * 0.25);
      return { credits, amountLkr, name: "Custom Pack" };
    }
    const pkg = packages.find((p) => p.id === selectedId) || packages[1];
    return {
      credits: pkg ? pkg.credits : 10000,
      amountLkr: pkg ? pkg.amount_lkr : 2500,
      name: pkg ? pkg.name : "Standard Pack",
    };
  };

  const handlePayHereCheckout = async () => {
    try {
      setLoading(true);

      const payload = {
        package_id: selectedId,
        custom_credits: selectedId === "custom" ? customCredits : null,
      };

      const res = await axios.post("/api/payments/initiate", payload);
      const initiateData = res.data?.data;

      if (!initiateData?.payhere_params) {
        throw new Error("Invalid payment parameters received.");
      }

      const payhereParams = initiateData.payhere_params;
      const orderId = initiateData.order_id;

      // Verify PayHere JS library loaded
      if (typeof window === "undefined" || !(window as any).payhere) {
        throw new Error("PayHere checkout library is still initializing. Please try again.");
      }

      const payhere = (window as any).payhere;

      payhere.onCompleted = async function onCompleted(completedOrderId: string) {
        toast.success("Payment completed! Updating your balance...");
        try {
          // Immediately trigger confirmation for sandbox/dev
          await axios.post("/api/payments/sandbox/confirm", {
            order_id: completedOrderId || orderId,
          });
        } catch (e) {
          // If already fulfilled via IPN, that's fine
        }
        onSuccess();
        onOpenChange(false);
      };

      payhere.onDismissed = function onDismissed() {
        setLoading(false);
        toast.info("Payment window was dismissed.");
      };

      payhere.onError = function onError(error: any) {
        setLoading(false);
        toast.error(`Payment failed: ${error}`);
      };

      payhere.startPayment(payhereParams);
    } catch (err: any) {
      toast.error(err.response?.data?.error || err.message || "Failed to start payment.");
      setLoading(false);
    }
  };

  const currentSelection = getActiveAmount();

  return (
    <>
      <Script 
        src="https://www.payhere.lk/lib/payhere.js" 
        strategy="lazyOnload"
        onLoad={() => setPayhereReady(true)}
      />

      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-2xl sm:max-w-2xl overflow-y-auto max-h-[90vh]">
          <DialogHeader>
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-primary/10 rounded-lg text-primary">
                <Coins className="h-5 w-5" />
              </div>
              <DialogTitle className="text-xl">Top Up Credits</DialogTitle>
            </div>
            <DialogDescription>
              Purchase credits to run FastText leaf language identification, multi-page OCR, and corpus segmentation.
            </DialogDescription>
          </DialogHeader>

          {fetchingPackages ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="space-y-5 py-2">
              {/* Packages Grid */}
              <div className="grid gap-3 sm:grid-cols-3">
                {packages.map((pkg) => {
                  const isSelected = selectedId === pkg.id;
                  return (
                    <div
                      key={pkg.id}
                      onClick={() => setSelectedId(pkg.id)}
                      className={`relative flex flex-col justify-between p-4 rounded-xl border-2 cursor-pointer transition-all ${
                        isSelected
                          ? "border-primary bg-primary/5 shadow-sm ring-1 ring-primary"
                          : "border-gray-200 hover:border-gray-300 hover:bg-gray-50/50"
                      }`}
                    >
                      {pkg.popular && (
                        <Badge className="absolute -top-2.5 right-3 bg-primary text-white text-[10px] px-2 py-0.5">
                          <Sparkles className="h-3 w-3 mr-1" />
                          Most Popular
                        </Badge>
                      )}

                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-semibold text-sm">{pkg.name}</span>
                          {isSelected && <Check className="h-4 w-4 text-primary" />}
                        </div>
                        <p className="text-xs text-muted-foreground line-clamp-2 mb-3">
                          {pkg.description}
                        </p>
                      </div>

                      <div className="mt-2 pt-2 border-t border-gray-100">
                        <div className="text-xl font-bold text-foreground">
                          {pkg.credits.toLocaleString()} <span className="text-xs font-normal text-muted-foreground">Credits</span>
                        </div>
                        <div className="text-sm font-semibold text-primary">
                          LKR {pkg.amount_lkr.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Custom Credits Option */}
              <div 
                onClick={() => setSelectedId("custom")}
                className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                  selectedId === "custom" 
                    ? "border-primary bg-primary/5 shadow-sm ring-1 ring-primary" 
                    : "border-gray-200 hover:border-gray-300 hover:bg-gray-50/50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold text-sm">Custom Top-up Amount</span>
                    <Badge variant="outline" className="text-[10px]">Min. 1,000</Badge>
                  </div>
                  {selectedId === "custom" && <Check className="h-4 w-4 text-primary" />}
                </div>

                {selectedId === "custom" && (
                  <div className="mt-3 grid grid-cols-2 gap-4 items-center">
                    <div>
                      <Label htmlFor="custom-credits" className="text-xs text-muted-foreground">
                        Enter Desired Credits:
                      </Label>
                      <Input
                        id="custom-credits"
                        type="number"
                        min="1000"
                        step="500"
                        value={customCredits}
                        onChange={(e) => setCustomCredits(Math.max(1000, Number(e.target.value)))}
                        className="mt-1 h-9"
                      />
                    </div>
                    <div className="text-right">
                      <span className="text-xs text-muted-foreground">Total Price (LKR):</span>
                      <p className="text-lg font-bold text-primary">
                        LKR {(Math.round(customCredits * 0.25)).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* PayHere Security & Payment Method Badges */}
              <div className="rounded-lg bg-gray-50 p-4 border border-gray-100 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-muted-foreground">
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="h-5 w-5 text-green-600 flex-shrink-0" />
                  <span>
                    Secured by <strong>PayHere Sri Lanka</strong> (Sandbox Mode enabled)
                  </span>
                </div>
                <div className="flex items-center space-x-2 font-medium text-[11px] text-gray-600">
                  <span className="px-1.5 py-0.5 bg-white border rounded">Visa</span>
                  <span className="px-1.5 py-0.5 bg-white border rounded">Mastercard</span>
                  <span className="px-1.5 py-0.5 bg-white border rounded">eZ Cash</span>
                  <span className="px-1.5 py-0.5 bg-white border rounded">mCash</span>
                  <span className="px-1.5 py-0.5 bg-white border rounded">Genie</span>
                </div>
              </div>
            </div>
          )}

          <DialogFooter className="flex-col sm:flex-row gap-2 border-t pt-4">
            <div className="flex-1 text-left">
              <span className="text-xs text-muted-foreground">Selected Package:</span>
              <p className="text-sm font-semibold text-foreground">
                {currentSelection.name} ({currentSelection.credits.toLocaleString()} Credits) — LKR {currentSelection.amountLkr.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
                Cancel
              </Button>
              <Button 
                onClick={handlePayHereCheckout} 
                disabled={loading || fetchingPackages}
                className="bg-primary hover:bg-primary/90 min-w-[170px]"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Launching PayHere...
                  </>
                ) : (
                  <>
                    <CreditCard className="mr-2 h-4 w-4" />
                    Pay with PayHere
                  </>
                )}
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
