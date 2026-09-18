"use client";

import { useState, useEffect } from "react";
import { ApprovalRequestCard } from "@/components/portal/ApprovalRequestCard";
import { fetchApprovals, updateApprovalStatus } from "@/lib/api/approvals";

interface PortalApproval {
  id: string;
  entityType: string;
  title: string;
  status: string;
  createdAt: string;
}

export default function PortalPage() {
  const [approvals, setApprovals] = useState<PortalApproval[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const data = await fetchApprovals("PENDING");
        // We map it to the structure ApprovalRequestCard expects. 
        // Note: ApprovalRequestCard expects entityType, createdAt, title, etc.
        setApprovals(data.items.map(item => ({
          id: item.id,
          entityType: item.entity_type,
          title: `${item.entity_type} Campaign`, // Fallback title
          status: item.status,
          createdAt: item.created_at,
        })));
      } catch (err) {
        console.error("Failed to load approvals", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleStatusChange = async (id: string, newStatus: string, comments?: string) => {
    try {
      await updateApprovalStatus(id, newStatus, comments);
      setApprovals((prev) => prev.filter(app => app.id !== id)); // Remove from pending
    } catch (err) {
      console.error("Failed to update status", err);
      alert("Failed to update status.");
    }
  };

  return (
    <div className="space-y-6">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 tracking-tight">Pending Approvals</h2>
        <p className="mt-2 text-sm text-gray-500">
          Review and approve campaigns and social posts crafted by your agency.
        </p>
      </div>

      {loading ? (
        <div className="py-12 text-center text-gray-500">Loading approvals...</div>
      ) : approvals.length === 0 ? (
        <div className="py-12 text-center text-gray-500">No pending approvals found.</div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {approvals.map((approval) => (
            <ApprovalRequestCard
              key={approval.id}
              approval={approval}
              onStatusChange={handleStatusChange}
            />
          ))}
        </div>
      )}
    </div>
  );
}
