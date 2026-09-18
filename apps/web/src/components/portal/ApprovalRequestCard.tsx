import { useState } from "react";
import { formatDistanceToNow } from "date-fns";
import { CheckCircle, MessageSquare, AlertCircle } from "lucide-react";

interface ApprovalRequest {
  id: string;
  entityType: string;
  title: string;
  status: string;
  createdAt: string;
}

interface ApprovalRequestCardProps {
  approval: ApprovalRequest;
  onStatusChange: (id: string, status: string, comments?: string) => void;
}

export function ApprovalRequestCard({ approval, onStatusChange }: ApprovalRequestCardProps) {
  const [comments, setComments] = useState("");
  const [showRejectInput, setShowRejectInput] = useState(false);

  const statusColors: Record<string, string> = {
    PENDING: "bg-yellow-100 text-yellow-800",
    APPROVED: "bg-green-100 text-green-800",
    REJECTED: "bg-red-100 text-red-800",
    CHANGES_REQUESTED: "bg-orange-100 text-orange-800",
  };

  const handleApprove = () => {
    onStatusChange(approval.id, "APPROVED");
  };

  const handleReject = () => {
    if (comments.trim() === "") {
      alert("Please provide feedback for the rejection or changes requested.");
      return;
    }
    onStatusChange(approval.id, "CHANGES_REQUESTED", comments);
    setShowRejectInput(false);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
      <div className="p-5">
        <div className="flex justify-between items-start mb-4">
          <div>
            <span className="inline-flex items-center rounded-md bg-indigo-50 px-2 py-1 text-xs font-medium text-indigo-700 ring-1 ring-inset ring-indigo-700/10 mb-2">
              {approval.entityType}
            </span>
            <h3 className="text-lg font-semibold text-gray-900 line-clamp-1">{approval.title}</h3>
            <p className="text-xs text-gray-500 mt-1">
              Created {formatDistanceToNow(new Date(approval.createdAt))} ago
            </p>
          </div>
          <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColors[approval.status]}`}>
            {approval.status.replace("_", " ")}
          </span>
        </div>

        {approval.status === "PENDING" && (
          <div className="mt-6">
            {!showRejectInput ? (
              <div className="flex gap-3">
                <button
                  onClick={handleApprove}
                  className="flex-1 inline-flex justify-center items-center gap-2 rounded-md bg-green-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-600 transition-colors"
                >
                  <CheckCircle className="w-4 h-4" />
                  Approve
                </button>
                <button
                  onClick={() => setShowRejectInput(true)}
                  className="flex-1 inline-flex justify-center items-center gap-2 rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 transition-colors"
                >
                  <MessageSquare className="w-4 h-4" />
                  Request Changes
                </button>
              </div>
            ) : (
              <div className="space-y-3 animate-in fade-in slide-in-from-top-2 duration-200">
                <label htmlFor="comments" className="block text-sm font-medium leading-6 text-gray-900">
                  Feedback for Agency
                </label>
                <div className="mt-2">
                  <textarea
                    id="comments"
                    name="comments"
                    rows={3}
                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                    placeholder="What needs to be changed?"
                    value={comments}
                    onChange={(e) => setComments(e.target.value)}
                  />
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={handleReject}
                    className="flex-1 inline-flex justify-center items-center gap-2 rounded-md bg-orange-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-orange-500 transition-colors"
                  >
                    <AlertCircle className="w-4 h-4" />
                    Submit Feedback
                  </button>
                  <button
                    onClick={() => setShowRejectInput(false)}
                    className="flex-1 inline-flex justify-center items-center gap-2 rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
