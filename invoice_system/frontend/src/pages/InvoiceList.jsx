import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listInvoices } from "../api/invoiceApi";
import StatusBadge from "../components/StatusBadge";

function formatAmount(value, currency) {
  if (value == null) return "-";
  const sym = currency === "EUR" ? "€" : currency === "GBP" ? "£" : "$";
  return `${sym}${Number(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export default function InvoiceList() {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    listInvoices()
      .then(setInvoices)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleRefresh = () => {
    setLoading(true);
    setError(null);
    listInvoices()
      .then(setInvoices)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  return (
    <>
      <div className="page-header flex-between">
        <div>
          <h1>Invoices</h1>
          <p>All processed invoices stored in the system.</p>
        </div>
        <div className="flex-row">
          <button className="btn btn-secondary btn-sm" onClick={handleRefresh}>
            Refresh
          </button>
          <button className="btn btn-primary btn-sm" onClick={() => navigate("/upload")}>
            Upload Invoice
          </button>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        {loading ? (
          <div className="spinner-wrapper"><div className="spinner" /></div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Filename</th>
                  <th>Supplier</th>
                  <th>Invoice No.</th>
                  <th>Date</th>
                  <th>Total</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {invoices.length === 0 && (
                  <tr>
                    <td colSpan={7} className="text-muted" style={{ textAlign: "center", padding: "32px" }}>
                      No invoices found. Upload one to get started.
                    </td>
                  </tr>
                )}
                {invoices.map((inv) => (
                  <tr
                    key={inv.id}
                    style={{ cursor: "pointer" }}
                    onClick={() => navigate(`/invoices/${inv.id}`)}
                  >
                    <td style={{ color: "var(--color-text-muted)", fontWeight: 500 }}>#{inv.id}</td>
                    <td style={{ maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {inv.filename}
                    </td>
                    <td>{inv.supplier_name ?? <span className="text-muted">-</span>}</td>
                    <td>{inv.invoice_number ?? <span className="text-muted">-</span>}</td>
                    <td>{inv.invoice_date ?? <span className="text-muted">-</span>}</td>
                    <td style={{ fontVariantNumeric: "tabular-nums" }}>
                      {formatAmount(inv.total_amount, inv.currency)}
                    </td>
                    <td><StatusBadge status={inv.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
