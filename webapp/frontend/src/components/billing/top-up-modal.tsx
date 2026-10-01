"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
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
import { 
  Loader2, 
  Coins, 
  Check, 
  ShieldCheck, 
  Sparkles, 
  CreditCard, 
  Smartphone, 
  Building2, 
  CheckCircle2, 
  Lock,
  ArrowRight,
  ChevronLeft
} from "lucide-react";

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

  // PayHere Sandbox Simulator State (For local demo & Viva presentation)
  const [showSandboxGateway, setShowSandboxGateway] = useState(false);
  const [activePaymentMethod, setActivePaymentMethod] = useState<"card" | "wallet" | "bank">("card");
  const [currentOrderId, setCurrentOrderId] = useState<string>("");
  const [currentOrderAmount, setCurrentOrderAmount] = useState<number>(2500);
  const [currentCreditsAmount, setCurrentCreditsAmount] = useState<number>(10000);
  const [currentPackageName, setCurrentPackageName] = useState<string>("Standard Researcher Pack");
  const [processingPayment, setProcessingPayment] = useState(false);
  const [paymentStep, setPaymentStep] = useState<"form" | "authorizing" | "success">("form");

  // Form Fields
  const [cardNumber, setCardNumber] = useState("4111 •••• •••• 1111");
  const [cardExpiry, setCardExpiry] = useState("12 / 28");
  const [cardCvv, setCardCvv] = useState("123");
  const [cardHolder, setCardHolder] = useState("Maleesha Kumarasinghe");
  const [walletPhone, setWalletPhone] = useState("077 123 4567");
  const [walletType, setWalletType] = useState("eZ Cash");
  const [selectedBank, setSelectedBank] = useState("Sampath Vishwa");

  useEffect(() => {
    if (!open) {
      setShowSandboxGateway(false);
      setPaymentStep("form");
      return;
    }

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

  const getActiveAmount = (): { credits: number; amountLkr: number; name: string } => {
    const stdPkg = packages.find((p) => p.id === "standard") || packages[0];
    const unitPrice = stdPkg && stdPkg.credits > 0 ? (stdPkg.amount_lkr / stdPkg.credits) : 0.25;

    if (selectedId === "custom") {
      const credits = Math.max(1000, Number(customCredits) || 1000);
      const amountLkr = Math.round(credits * unitPrice);
      return { credits, amountLkr, name: "Custom Pack" };
    }
    const pkg = packages.find((p) => p.id === selectedId) || packages[1] || packages[0];
    return {
      credits: pkg ? pkg.credits : 10000,
      amountLkr: pkg ? pkg.amount_lkr : 2500,
      name: pkg ? pkg.name : "Standard Researcher Pack",
    };
  };

  const handleLaunchPayHere = async () => {
    try {
      setLoading(true);

      const payload = {
        package_id: selectedId,
        custom_credits: selectedId === "custom" ? customCredits : null,
      };

      // 1. Call Backend to create pending order and generate official PayHere hash
      const res = await axios.post("/api/payments/initiate", payload);
      const initiateData = res.data?.data;

      if (!initiateData?.order_id) {
        throw new Error("Invalid payment parameters received.");
      }

      setCurrentOrderId(initiateData.order_id);
      setCurrentOrderAmount(initiateData.amount_lkr);
      setCurrentCreditsAmount(initiateData.credits_amount);
      setCurrentPackageName(initiateData.package_name);

      // Launch the Sandbox Gateway interface
      setShowSandboxGateway(true);
      setPaymentStep("form");
      setLoading(false);
    } catch (err: any) {
      toast.error(err.response?.data?.error || err.message || "Failed to initialize payment.");
      setLoading(false);
    }
  };

  const handleConfirmSandboxPayment = async () => {
    try {
      setProcessingPayment(true);
      setPaymentStep("authorizing");

      // Realistic 3D-Secure bank simulation delay
      await new Promise((r) => setTimeout(r, 1400));

      // 2. Call backend to confirm and atomically credit balance in PostgreSQL
      await axios.post("/api/payments/sandbox/confirm", {
        order_id: currentOrderId,
      });

      setPaymentStep("success");
      setProcessingPayment(false);
      toast.success(`Successfully added ${currentCreditsAmount.toLocaleString()} credits to your account!`);

      // Refresh balance in dashboard
      onSuccess();
    } catch (err: any) {
      setProcessingPayment(false);
      setPaymentStep("form");
      toast.error(err.response?.data?.detail || "Payment authorization failed.");
    }
  };

  const currentSelection = getActiveAmount();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl sm:max-w-2xl overflow-hidden p-0 border border-slate-200/80 shadow-2xl rounded-2xl bg-white">
        {!showSandboxGateway ? (
          /* ================= STEP 1: PACKAGE SELECTION MODAL ================= */
          <div className="p-6 space-y-5">
            <DialogHeader>
              <div className="flex items-center space-x-3">
                <div className="p-2.5 bg-primary/10 rounded-xl text-primary">
                  <Coins className="h-6 w-6" />
                </div>
                <div>
                  <DialogTitle className="text-xl font-bold tracking-tight">Top Up Credits</DialogTitle>
                  <DialogDescription className="text-xs text-muted-foreground mt-0.5">
                    Select a credit tier to run FastText language identification and OCR document analysis.
                  </DialogDescription>
                </div>
              </div>
            </DialogHeader>

            {fetchingPackages ? (
              <div className="flex justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <div className="space-y-4">
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
                            : "border-slate-200 hover:border-slate-300 hover:bg-slate-50/60"
                        }`}
                      >
                        {pkg.popular && (
                          <Badge className="absolute -top-2.5 right-3 bg-primary text-white text-[10px] px-2 py-0.5 shadow-sm">
                            <Sparkles className="h-3 w-3 mr-1" />
                            Most Popular
                          </Badge>
                        )}

                        <div>
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-semibold text-sm text-foreground">{pkg.name}</span>
                            {isSelected && <Check className="h-4 w-4 text-primary" />}
                          </div>
                          <p className="text-xs text-muted-foreground line-clamp-2 mb-3">
                            {pkg.description}
                          </p>
                        </div>

                        <div className="mt-2 pt-2 border-t border-slate-100">
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
                      : "border-slate-200 hover:border-slate-300 hover:bg-slate-50/60"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-sm text-foreground">Custom Top-up Amount</span>
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
                          LKR {(Math.round(customCredits * (packages.find((p) => p.id === "standard")?.amount_lkr && packages.find((p) => p.id === "standard")!.credits > 0 ? (packages.find((p) => p.id === "standard")!.amount_lkr / packages.find((p) => p.id === "standard")!.credits) : 0.25))).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                {/* PayHere Security & Payment Method Badges */}
                <div className="rounded-xl bg-slate-50 p-4 border border-slate-200/80 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-600">
                  <div className="flex items-center space-x-2">
                    <ShieldCheck className="h-5 w-5 text-emerald-600 flex-shrink-0" />
                    <span>
                      Secured by <strong>PayHere Sri Lanka</strong> (CBSL Approved Sandbox)
                    </span>
                  </div>
                  <div className="flex items-center space-x-1.5 font-medium text-[11px] text-slate-600">
                    <span className="px-1.5 py-0.5 bg-white border border-slate-200 rounded">Visa</span>
                    <span className="px-1.5 py-0.5 bg-white border border-slate-200 rounded">Mastercard</span>
                    <span className="px-1.5 py-0.5 bg-white border border-slate-200 rounded">eZ Cash</span>
                    <span className="px-1.5 py-0.5 bg-white border border-slate-200 rounded">mCash</span>
                    <span className="px-1.5 py-0.5 bg-white border border-slate-200 rounded">Genie</span>
                  </div>
                </div>
              </div>
            )}

            <DialogFooter className="flex-col sm:flex-row gap-3 border-t border-slate-100 pt-4">
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
                  onClick={handleLaunchPayHere} 
                  disabled={loading || fetchingPackages}
                  className="bg-primary hover:bg-primary/90 text-white min-w-[170px]"
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Connecting...
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
          </div>
        ) : (
          /* ================= STEP 2: BALANCED PAYHERE SANDBOX GATEWAY MODAL ================= */
          <div className="flex flex-col bg-white">
            {/* Header: Polished Navy Gradient with Safe Margin for Close Button */}
            <div className="bg-gradient-to-r from-[#0b2447] via-[#19376d] to-[#0b2447] px-6 py-5 text-white flex items-center justify-between border-b border-blue-900/30">
              <div className="flex items-center space-x-3.5">
                <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center p-1.5 shadow-sm">
                  <div className="text-[#0b2447] font-black text-sm tracking-tight flex items-center">
                    Pay<span className="text-amber-500">Here</span>
                  </div>
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="font-bold text-base tracking-tight text-white">PayHere Sandbox Checkout</h3>
                    <Badge className="bg-amber-400/20 text-amber-300 border-amber-400/40 text-[10px] font-medium py-0 px-1.5">
                      Sandbox Mode
                    </Badge>
                  </div>
                  <p className="text-xs text-blue-200/90 mt-0.5">
                    Order: <span className="font-mono text-amber-300 font-semibold">{currentOrderId}</span> • LangID Platform
                  </p>
                </div>
              </div>

              {/* Amount Box: Padded cleanly on the right to never collide with the modal X button */}
              <div className="text-right pr-9">
                <span className="text-[11px] uppercase tracking-wider text-blue-200/80 font-medium block">Amount Due</span>
                <p className="text-xl font-extrabold text-white tracking-tight">
                  LKR {currentOrderAmount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </p>
              </div>
            </div>

            {/* Modal Body */}
            <div className="p-6 bg-slate-50/70">
              {paymentStep === "form" && (
                <div className="space-y-5">
                  {/* Clean, Balanced Tabs */}
                  <div className="grid grid-cols-3 gap-2.5 p-1.5 bg-slate-200/70 rounded-xl border border-slate-200">
                    <button
                      onClick={() => setActivePaymentMethod("card")}
                      className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold transition-all ${
                        activePaymentMethod === "card"
                          ? "bg-white text-slate-900 shadow-sm border border-slate-200/80"
                          : "text-slate-600 hover:text-slate-900 hover:bg-white/50"
                      }`}
                    >
                      <CreditCard className="h-4 w-4 text-blue-600" />
                      Card (Visa/Master)
                    </button>
                    <button
                      onClick={() => setActivePaymentMethod("wallet")}
                      className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold transition-all ${
                        activePaymentMethod === "wallet"
                          ? "bg-white text-slate-900 shadow-sm border border-slate-200/80"
                          : "text-slate-600 hover:text-slate-900 hover:bg-white/50"
                      }`}
                    >
                      <Smartphone className="h-4 w-4 text-emerald-600" />
                      eZ Cash / mCash
                    </button>
                    <button
                      onClick={() => setActivePaymentMethod("bank")}
                      className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold transition-all ${
                        activePaymentMethod === "bank"
                          ? "bg-white text-slate-900 shadow-sm border border-slate-200/80"
                          : "text-slate-600 hover:text-slate-900 hover:bg-white/50"
                      }`}
                    >
                      <Building2 className="h-4 w-4 text-indigo-600" />
                      Internet Banking
                    </button>
                  </div>

                  {/* Tab 1: Credit / Debit Card Form */}
                  {activePaymentMethod === "card" && (
                    <div className="space-y-4 bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                      <div className="flex items-center justify-between text-xs text-slate-600 border-b border-slate-100 pb-2.5">
                        <span className="font-medium text-slate-700">Pre-filled Sandbox Test Card</span>
                        <span className="text-emerald-600 font-medium flex items-center gap-1">
                          <Lock className="h-3 w-3" /> 256-bit SSL Encrypted
                        </span>
                      </div>

                      <div className="space-y-3.5">
                        <div>
                          <Label className="text-xs font-medium text-slate-600">Card Number</Label>
                          <div className="relative mt-1">
                            <Input 
                              value={cardNumber} 
                              onChange={(e) => setCardNumber(e.target.value)} 
                              className="bg-white border-slate-200 text-slate-900 font-mono text-sm pl-3 pr-20 h-10 shadow-sm" 
                            />
                            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center space-x-1.5 text-[10px] font-bold text-slate-400">
                              <span className="px-1.5 py-0.5 bg-blue-50 text-blue-700 border border-blue-200 rounded">VISA</span>
                              <span className="px-1.5 py-0.5 bg-amber-50 text-amber-700 border border-amber-200 rounded">MC</span>
                            </div>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-3.5">
                          <div>
                            <Label className="text-xs font-medium text-slate-600">Expiration Date</Label>
                            <Input 
                              value={cardExpiry} 
                              onChange={(e) => setCardExpiry(e.target.value)} 
                              className="bg-white border-slate-200 text-slate-900 font-mono text-sm mt-1 h-10 shadow-sm" 
                            />
                          </div>
                          <div>
                            <Label className="text-xs font-medium text-slate-600">CVV / CVC</Label>
                            <Input 
                              value={cardCvv} 
                              onChange={(e) => setCardCvv(e.target.value)} 
                              className="bg-white border-slate-200 text-slate-900 font-mono text-sm mt-1 h-10 shadow-sm" 
                            />
                          </div>
                        </div>

                        <div>
                          <Label className="text-xs font-medium text-slate-600">Cardholder Name</Label>
                          <Input 
                            value={cardHolder} 
                            onChange={(e) => setCardHolder(e.target.value)} 
                            className="bg-white border-slate-200 text-slate-900 text-sm mt-1 h-10 shadow-sm" 
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tab 2: Mobile Wallet Form */}
                  {activePaymentMethod === "wallet" && (
                    <div className="space-y-4 bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                      <div className="flex items-center justify-between text-xs text-slate-600 border-b border-slate-100 pb-2.5">
                        <span className="font-medium text-slate-700">Mobile Wallet Debit Simulation</span>
                        <span className="text-emerald-600 font-medium flex items-center gap-1">
                          <Lock className="h-3 w-3" /> Secure USSD Channel
                        </span>
                      </div>

                      <div className="space-y-3.5">
                        <div className="grid grid-cols-2 gap-3.5">
                          <div>
                            <Label className="text-xs font-medium text-slate-600">Wallet Operator</Label>
                            <select
                              value={walletType}
                              onChange={(e) => setWalletType(e.target.value)}
                              className="w-full bg-white border border-slate-200 text-slate-900 rounded-md px-3 h-10 text-sm mt-1 shadow-sm"
                            >
                              <option value="eZ Cash">Dialog eZ Cash</option>
                              <option value="mCash">Mobitel mCash</option>
                              <option value="Genie">Genie by Dialog</option>
                            </select>
                          </div>
                          <div>
                            <Label className="text-xs font-medium text-slate-600">Registered Mobile Number</Label>
                            <Input 
                              value={walletPhone} 
                              onChange={(e) => setWalletPhone(e.target.value)} 
                              className="bg-white border-slate-200 text-slate-900 font-mono text-sm mt-1 h-10 shadow-sm" 
                            />
                          </div>
                        </div>
                        <p className="text-xs text-muted-foreground bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                          In test mode, clicking authorize simulates instant mobile wallet confirmation and balance settlement.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Tab 3: Internet Banking Form */}
                  {activePaymentMethod === "bank" && (
                    <div className="space-y-4 bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                      <div className="flex items-center justify-between text-xs text-slate-600 border-b border-slate-100 pb-2.5">
                        <span className="font-medium text-slate-700">Sri Lankan Bank IPG Direct Clearing</span>
                        <span className="text-emerald-600 font-medium flex items-center gap-1">
                          <Lock className="h-3 w-3" /> CBSL Direct Clearing
                        </span>
                      </div>

                      <div className="space-y-3.5">
                        <div>
                          <Label className="text-xs font-medium text-slate-600">Select Bank</Label>
                          <select
                            value={selectedBank}
                            onChange={(e) => setSelectedBank(e.target.value)}
                            className="w-full bg-white border border-slate-200 text-slate-900 rounded-md px-3 h-10 text-sm mt-1 shadow-sm"
                          >
                            <option value="Sampath Vishwa">Sampath Bank (Sampath Vishwa)</option>
                            <option value="Commercial Bank">Commercial Bank (ComBank Digital)</option>
                            <option value="HNB">Hatton National Bank (HNB Digital)</option>
                            <option value="Frimi">Frimi (Nations Trust Bank)</option>
                          </select>
                        </div>
                        <p className="text-xs text-muted-foreground bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                          Simulates real-time bank internet banking API authentication and automated credit receipt.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Balanced Footer Actions */}
                  <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-slate-200/80">
                    <div className="text-left w-full sm:w-auto">
                      <span className="text-xs text-muted-foreground">Settling:</span>
                      <p className="text-xs font-semibold text-slate-800">
                        {currentPackageName} (<span className="text-emerald-600 font-bold">+{currentCreditsAmount.toLocaleString()} Credits</span>)
                      </p>
                    </div>
                    <div className="flex items-center space-x-2.5 w-full sm:w-auto justify-end">
                      <Button 
                        variant="outline" 
                        onClick={() => setShowSandboxGateway(false)} 
                        className="border-slate-300 text-slate-700 hover:bg-slate-100 h-10 text-xs font-medium px-4"
                      >
                        <ChevronLeft className="h-4 w-4 mr-1" />
                        Back
                      </Button>
                      <Button 
                        onClick={handleConfirmSandboxPayment}
                        className="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs h-10 px-5 shadow-sm flex items-center gap-2"
                      >
                        <Lock className="h-3.5 w-3.5" />
                        Authorize & Pay LKR {currentOrderAmount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </Button>
                    </div>
                  </div>
                </div>
              )}

              {/* Authorizing Step */}
              {paymentStep === "authorizing" && (
                <div className="py-14 text-center space-y-4 bg-white rounded-xl border border-slate-200 shadow-sm p-6">
                  <div className="relative inline-block">
                    <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto" />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <Lock className="h-4 w-4 text-blue-700" />
                    </div>
                  </div>
                  <div>
                    <h4 className="text-base font-bold text-slate-900">Communicating with PayHere Clearing Network...</h4>
                    <p className="text-xs text-muted-foreground mt-1 max-w-md mx-auto">
                      Simulating 3D-Secure OTP authorization, validating cryptographic MD5 checksum, and updating PostgreSQL database row-locks.
                    </p>
                  </div>
                </div>
              )}

              {/* Success Step */}
              {paymentStep === "success" && (
                <div className="py-8 text-center space-y-5 bg-white rounded-xl border border-slate-200 shadow-sm p-6">
                  <div className="w-14 h-14 bg-emerald-50 text-emerald-600 rounded-full flex items-center justify-center mx-auto ring-8 ring-emerald-50/50">
                    <CheckCircle2 className="h-8 w-8 text-emerald-600" />
                  </div>
                  <div>
                    <h4 className="text-xl font-bold text-slate-900">Payment Approved & Settled!</h4>
                    <p className="text-xs text-muted-foreground mt-1">
                      PayHere confirmation received for Order <strong className="text-slate-800 font-mono">{currentOrderId}</strong>.
                    </p>
                  </div>

                  <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 max-w-md mx-auto text-left space-y-2 text-xs">
                    <div className="flex justify-between py-1 border-b border-slate-200/60">
                      <span className="text-muted-foreground">Payment Status:</span>
                      <span className="text-emerald-700 font-bold">COMPLETED (HTTP 200)</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-200/60">
                      <span className="text-muted-foreground">Amount Paid:</span>
                      <span className="text-slate-900 font-semibold">LKR {currentOrderAmount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-200/60">
                      <span className="text-muted-foreground">Credits Credited:</span>
                      <span className="text-emerald-700 font-bold">+{currentCreditsAmount.toLocaleString(undefined, { minimumFractionDigits: 4 })} Credits</span>
                    </div>
                    <div className="flex justify-between py-1">
                      <span className="text-muted-foreground">Database Action:</span>
                      <span className="text-slate-700 font-mono">Atomic row-lock balance incremented</span>
                    </div>
                  </div>

                  <div className="pt-2">
                    <Button 
                      onClick={() => {
                        setShowSandboxGateway(false);
                        onOpenChange(false);
                      }}
                      className="bg-primary hover:bg-primary/90 text-white font-semibold px-8 h-10 text-xs"
                    >
                      Return to Dashboard
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
