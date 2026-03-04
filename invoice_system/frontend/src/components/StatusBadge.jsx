import React from "react";

const CLASS_MAP = {
  completed:  "badge-completed",
  pending:    "badge-pending",
  processing: "badge-processing",
  failed:     "badge-failed",
};

/**
 * Renders a coloured status badge for an invoice processing status value.
 */
export default function StatusBadge({ status }) {
  const cls = CLASS_MAP[status] ?? "badge-pending";
  return <span className={`badge ${cls}`}>{status}</span>;
}
