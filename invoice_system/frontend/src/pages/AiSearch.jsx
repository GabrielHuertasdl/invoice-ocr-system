import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { searchInvoices } from "../api/invoiceApi";
import StatusBadge from "../components/StatusBadge";

function formatAmount(value, currency) {
  if (value == null) return "-";
  const sym = currency === "EUR" ? "€" : currency === "GBP" ? "£" : "$";
  return `${sym}${Number(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

const EXAMPLES = [
  "facturas de Acme Corp",
  "pdfs de DATAFLOW",
  "TechSupplies invoices",
];

export default function AiSearch() {
  const [query, setQuery]     = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);
  const navigate = useNavigate();

  const handleSearch = (q) => {
    const text = q ?? query;
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    setResults(null);
    searchInvoices(text.trim())
      .then(setResults)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  const handleKey = (e) => {
    if (e.key === "Enter") handleSearch();
  };

  return (
    <>
      <div className="page-header">
        <h1>AI Search</h1>
        <p>Search invoices using natural language — no exact names needed.</p>
      </div>

      {/* Search box */}
      <div className="card">
        <div className="ai-search-box">
          <input
            className="form-control ai-search-input"
            type="text"
            placeholder='e.g. "facturas de Acme Corp" or "DATAFLOW invoices"'
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKey}
          />
          <button
            className="btn btn-primary"
            onClick={() => handleSearch()}
            disabled={loading || !query.trim()}
          >
            {loading ? "Searching…" : "🔍 Search"}
          </button>
        </div>

        {/* Example queries */}
        <div className="ai-examples">
          <span className="text-muted" style={{ fontSize: 12 }}>Try: </span>
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              className="ai-example-chip"
              onClick={() => { setQuery(ex); handleSearch(ex); }}
            >
              {ex}
            </button>
          ))}
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Results */}
      {results !== null && (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--color-border)", background: "#f8fafc" }}>
            <span style={{ fontWeight: 600, fontSize: 14 }}>
              {results.length === 0
                ? "No invoices found"
                : `${results.length} invoice${results.length !== 1 ? "s" : ""} found`}
            </span>
            {results.length > 0 && (
              <span className="text-muted" style={{ fontSize: 12, marginLeft: 8 }}>
                — click a row to view details
              </span>
            )}
          </div>

          {results.length === 0 ? (
            <div style={{ padding: "32px", textAlign: "center", color: "var(--color-text-muted)" }}>
              Try a different query or upload more invoices.
            </div>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Supplier</th>
                    <th>Invoice No.</th>
                    <th>Date</th>
                    <th>Total</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((inv) => (
                    <tr
                      key={inv.id}
                      style={{ cursor: "pointer" }}
                      onClick={() => navigate(`/invoices/${inv.id}`)}
                    >
                      <td style={{ color: "var(--color-text-muted)", fontWeight: 500 }}>#{inv.id}</td>
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
      )}
    </>
  );
}
