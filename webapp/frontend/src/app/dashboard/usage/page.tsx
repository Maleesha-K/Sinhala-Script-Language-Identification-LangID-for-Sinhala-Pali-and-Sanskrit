"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { format } from "date-fns";
import { toast } from "sonner";
import Link from "next/link";
import { Loader2, Coins, Activity, FileText, CheckCircle2, Clock, XCircle, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/layout/page-header";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent } from "@/components/ui/card";

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

export default function UsagePage() {
  const [data, setData] = useState<UsageBreakdown | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUsage = async () => {
      try {
        const res = await axios.get("/api/usage");
        setData(res.data.data);
      } catch (error) {
        toast.error("Failed to load usage data.");
      } finally {
        setLoading(false);
      }
    };
    fetchUsage();
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
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Usage & Billing" 
        description="Track your credit balance and view recent activity charges." 
      />

      {loading ? (
        <div className="flex justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : data ? (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <Card className="bg-primary/5 border-primary/20">
              <CardContent className="p-6">
                <div className="flex items-center space-x-4">
                  <div className="p-3 bg-primary/10 rounded-full">
                    <Coins className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Available Credits</p>
                    <h3 className="text-3xl font-bold text-foreground">{data.credits_balance.toFixed(4)}</h3>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
            <div className="p-4 border-b bg-gray-50/50">
              <h3 className="font-medium">Activity Feed</h3>
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
                      <TableCell className="max-w-[300px] truncate" title={activity.name}>
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
        </>
      ) : (
        <div className="text-center py-12 text-muted-foreground">Error loading usage data.</div>
      )}
    </div>
  );
}
