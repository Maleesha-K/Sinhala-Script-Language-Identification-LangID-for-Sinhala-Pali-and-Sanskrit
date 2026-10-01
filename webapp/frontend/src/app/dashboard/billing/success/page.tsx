"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import axios from "axios";
import Link from "next/link";
import { CheckCircle2, Coins, ArrowRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

function BillingSuccessContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const orderId = searchParams.get("order_id");

  const [confirming, setConfirming] = useState(true);
  const [confirmed, setConfirmed] = useState(false);
  const [newBalance, setNewBalance] = useState<number | null>(null);

  useEffect(() => {
    const confirmPayment = async () => {
      if (!orderId) {
        setConfirming(false);
        return;
      }

      try {
        const res = await axios.post("/api/payments/sandbox/confirm", {
          order_id: orderId,
        });
        if (res.data?.data) {
          setConfirmed(true);
          if (res.data.data.new_balance !== undefined) {
            setNewBalance(res.data.data.new_balance);
          }
        }
      } catch (err) {
        // Even if this fails because IPN already handled it, show confirmation
        setConfirmed(true);
      } finally {
        setConfirming(false);
      }
    };

    confirmPayment();
  }, [orderId]);

  return (
    <div className="max-w-xl mx-auto py-12 px-4">
      <Card className="border-green-100 shadow-md">
        <CardContent className="p-8 text-center space-y-6">
          <div className="mx-auto w-16 h-16 bg-green-50 rounded-full flex items-center justify-center">
            {confirming ? (
              <Loader2 className="w-8 h-8 text-green-600 animate-spin" />
            ) : (
              <CheckCircle2 className="w-10 h-10 text-green-600" />
            )}
          </div>

          <div>
            <h2 className="text-2xl font-bold text-foreground">Payment Successful!</h2>
            <p className="text-sm text-muted-foreground mt-2">
              Your transaction has been processed securely through PayHere Sri Lanka.
            </p>
            {orderId && (
              <p className="text-xs font-mono text-muted-foreground mt-1 bg-gray-50 py-1 px-3 rounded inline-block">
                Order ID: {orderId}
              </p>
            )}
          </div>

          {newBalance !== null && (
            <div className="p-4 bg-primary/5 rounded-xl border border-primary/20 flex items-center justify-center space-x-3">
              <Coins className="h-6 w-6 text-primary" />
              <div className="text-left">
                <p className="text-xs text-muted-foreground">Updated Available Balance</p>
                <p className="text-lg font-bold text-foreground">
                  {newBalance.toLocaleString(undefined, { minimumFractionDigits: 4 })} Credits
                </p>
              </div>
            </div>
          )}

          <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2">
            <Link href="/dashboard/usage">
              <Button variant="outline" className="w-full sm:w-auto">
                View Usage & History
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button className="w-full sm:w-auto bg-primary hover:bg-primary/90 flex items-center gap-2">
                Continue to Dashboard
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function BillingSuccessPage() {
  return (
    <Suspense fallback={<div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin" /></div>}>
      <BillingSuccessContent />
    </Suspense>
  );
}
