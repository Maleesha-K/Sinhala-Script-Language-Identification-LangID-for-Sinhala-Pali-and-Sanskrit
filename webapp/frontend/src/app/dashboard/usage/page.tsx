"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { format } from "date-fns";
import { toast } from "sonner";
import Link from "next/link";
import { 
  Loader2, 
  Coins, 
  Activity, 
  FileText, 
  CheckCircle2, 
  Clock, 
  XCircle, 
  Eye, 
  PlusCircle, 
  Receipt, 
  CreditCard,
  Ban,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/layout/page-header";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TopUpModal } from "@/components/billing/top-up-modal";
import { useAuth } from "@/context/auth-context";

interface ActivityItem {
  id: string;
  activity_type: "classification" | "ocr";
  name: string;
  status: string;
  cost: number;
  created_at: string;
}

interface UsageBreakdown {
  credits_balance: number;
  activities: ActivityItem[];
}

interface PaymentRecord {
  id: string;
  order_id: string;
  package_name: string;
  amount_lkr: number;
  currency: string;
  credits_amount: number;
  status: string;
  payment_method: string | null;
  created_at: string;
  completed_at: string | null;
}

export default function UsagePage() {
  const [data, setData] = useState<UsageBreakdown | null>(null);
  const [payments, setPayments] = useState<PaymentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [topUpOpen, setTopUpOpen] = useState(false);
  const { refreshUser } = useAuth();

  const fetchUsageAndPayments = async () => {
    try {
      const [usageRes, paymentsRes] = await Promise.all([
        axios.get("/api/usage"),
        axios.get("/api/payments/history").catch(() => ({ data: { data: [] } })),
      ]);

      setData(usageRes.data.data);
      if (paymentsRes.data?.data) {
        setPayments(paymentsRes.data.data);
      }
      if (typeof window !== "undefined") {
        window.dispatchEvent(new Event("credits-updated"));
      }
    } catch (error) {
      toast.error("Failed to load usage data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsageAndPayments();
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case "completed":
      case "ready":
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case "queued":
      case "processing":
      case "uploading":
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case "failed":
      case "deleted":
        return <XCircle className="h-4 w-4 text-red-500" />;
      case "cancelled":
        return <Ban className="h-4 w-4 text-amber-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getPaymentStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "completed":
        return <Badge className="bg-green-100 text-green-800 hover:bg-green-100 border-green-200">Completed</Badge>;
      case "pending":
        return <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100 border-yellow-200">Pending</Badge>;
      case "cancelled":
        return <Badge className="bg-gray-100 text-gray-800 hover:bg-gray-100 border-gray-200">Cancelled</Badge>;
      case "failed":
        return <Badge className="bg-red-100 text-red-800 hover:bg-red-100 border-red-200">Failed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <PageHeader 
          title="Usage & Billing" 
          description="Track your credit balance, purchase top-ups with PayHere Sri Lanka, and view recent activity charges." 
        />
        <Button 
          onClick={() => setTopUpOpen(true)}
          className="bg-primary hover:bg-primary/90 text-white shadow-sm flex items-center gap-2"
        >
          <PlusCircle className="h-4 w-4" />
          Top Up Credits
        </Button>
      </div>

      {loading ? (
        <div className="flex justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : data ? (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <Card className="bg-primary/5 border-primary/20 md:col-span-2">
              <CardContent className="p-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-center space-x-4">
                    <div className="p-3 bg-primary/10 rounded-full">
                      <Coins className="h-7 w-7 text-primary" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Available Credits</p>
                      <h3 className="text-3xl font-bold text-foreground">
                        {data.credits_balance.toLocaleString(undefined, { minimumFractionDigits: 4, maximumFractionDigits: 4 })}
                      </h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        Credits are charged per page for OCR extraction and per token for language classification.
                      </p>
                    </div>
                  </div>
                  <Button 
                    onClick={() => setTopUpOpen(true)}
                    variant="outline" 
                    className="border-primary/30 hover:bg-primary/10 text-primary self-start sm:self-auto"
                  >
                    Buy More Credits
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card className="border-gray-200">
              <CardContent className="p-6 flex flex-col justify-between h-full">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-muted-foreground">Local Payment Gateway</span>
                    <Badge variant="outline" className="text-[10px] text-green-700 bg-green-50 border-green-200">
                      Sandbox Active
                    </Badge>
                  </div>
                  <p className="text-base font-semibold text-foreground">PayHere Sri Lanka</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Accepting LKR Visa/Mastercard, eZ Cash, mCash, & local online bank transfers.
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-gray-100 flex items-center gap-1 text-[11px] text-muted-foreground">
                  <CreditCard className="h-3.5 w-3.5" />
                  <span>Instant balance credit upon confirmation</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Activity Feed */}
          <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
            <div className="p-4 border-b bg-gray-50/50 flex items-center justify-between">
              <h3 className="font-medium text-foreground">Usage Activity Feed</h3>
              <span className="text-xs text-muted-foreground">Charges applied to balance</span>
            </div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Item</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Cost</TableHead>
                  <TableHead className="text-center w-[60px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.activities.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                      No recent activity.
                    </TableCell>
                  </TableRow>
                ) : (
                  data.activities.map((activity) => (
                    <TableRow key={activity.id}>
                      <TableCell className="whitespace-nowrap">
                        {format(new Date(activity.created_at), "MMM d, yyyy HH:mm")}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {activity.activity_type === "ocr" ? (
                            <FileText className="h-4 w-4 text-muted-foreground" />
                          ) : (
                            <Activity className="h-4 w-4 text-muted-foreground" />
                          )}
                          <span className="capitalize">{activity.activity_type}</span>
                        </div>
                      </TableCell>
                      <TableCell className="max-w-[300px] xl:max-w-[560px] truncate" title={activity.name}>
                        {activity.name}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(activity.status)}
                          <span className="capitalize text-sm">{activity.status.toLowerCase()}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right font-medium text-red-600">
                        {activity.cost > 0 ? `-${activity.cost.toFixed(4)}` : "0.0000"}
                      </TableCell>
                      <TableCell className="text-center">
                        <Link 
                          href={activity.activity_type === "ocr" 
                            ? `/dashboard/documents/${activity.id}` 
                            : `/dashboard/classification/${activity.id}`
                          }
                        >
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-primary">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {/* Payment & Top-Up History */}
          <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
            <div className="p-4 border-b bg-gray-50/50 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Receipt className="h-4 w-4 text-muted-foreground" />
                <h3 className="font-medium text-foreground">Payment & Top-Up History</h3>
              </div>
              <span className="text-xs text-muted-foreground">Transactions via PayHere</span>
            </div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Order ID</TableHead>
                  <TableHead>Package</TableHead>
                  <TableHead>Payment Method</TableHead>
                  <TableHead className="text-right">Amount (LKR)</TableHead>
                  <TableHead className="text-right">Credits Added</TableHead>
                  <TableHead className="text-center">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {payments.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                      No payment transactions yet. Click &quot;Top Up Credits&quot; to purchase a package.
                    </TableCell>
                  </TableRow>
                ) : (
                  payments.map((p) => (
                    <TableRow key={p.id}>
                      <TableCell className="whitespace-nowrap">
                        {format(new Date(p.created_at), "MMM d, yyyy HH:mm")}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground">
                        {p.order_id}
                      </TableCell>
                      <TableCell className="font-medium">
                        {p.package_name}
                      </TableCell>
                      <TableCell className="text-muted-foreground text-sm">
                        {p.payment_method || "PayHere"}
                      </TableCell>
                      <TableCell className="text-right font-semibold">
                        LKR {Number(p.amount_lkr).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </TableCell>
                      <TableCell className="text-right font-medium text-green-600">
                        +{Number(p.credits_amount).toLocaleString()}
                      </TableCell>
                      <TableCell className="text-center">
                        {getPaymentStatusBadge(p.status)}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </>
      ) : (
        <div className="text-center py-12 text-muted-foreground">Error loading usage data.</div>
      )}

      {/* Top-up modal */}
      <TopUpModal 
        open={topUpOpen} 
        onOpenChange={setTopUpOpen} 
        onSuccess={() => { fetchUsageAndPayments(); refreshUser(); }} 
      />
    </div>
  );
}
