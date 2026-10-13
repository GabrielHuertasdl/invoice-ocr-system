import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getInvoice, updateInvoice, qaInvoice } from "../api/invoiceApi";
import StatusBadge from "../components/StatusBadge";
import LineItemsTable from "../components/LineItemsTable";

const FIELDS = [
  { key: "supplier_name",  label: "Supplier Name",  type: "text" },
  { key: "invoice_number", label: "Invoice Number", type: "text" },
  { key: "invoice_date",   label: "Invoice Date",   type: "text" },
  { key: "due_date",       label: "Due Date",        type: "text" },
  { key: "currency",       label: "Currency",        type: "text" },
  { key: "subtotal",       label: "Subtotal",        type: "number" },
  { key: "tax_amount",     label: "Tax Amount",      type: "number" },
  { key: "total_amount",   label: "Total Amount",    type: "number" },
];

export default function InvoiceDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [invoice, setInvoice] = useState(null);
  const [form, setForm]       = useState({});
  const [lineItems, setLineItems] = useState([]);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving]   = useState(false);
  const [error, setError]     = useState(null);
  const [saved, setSaved]     = useState(false);
  const [loading, setLoading] = useState(true);
  const [showRaw, setShowRaw] = useState(false);

  // AI QA state
  const [qaQuestion, setQaQuestion]   = useState("");
  const [qaAnswer, setQaAnswer]       = useState(null);
  const [qaLoading, setQaLoading]     = useState(false);
  const [qaError, setQaError]         = useState(null);

  const handleAsk = async () => {
    if (!qaQuestion.trim()) return;
    setQaLoading(true);
    setQaError(null);
    setQaAnswer(null);
    try {
      const res = await qaInvoice(Number(id), qaQuestion.trim());
      setQaAnswer(res.answer);
    } catch (e) {
      setQaError(e.message);
    } finally {
      setQaLoading(false);
    }
  };

  useEffect(() => {
    getInvoice(id)
      .then((data) => {
        setInvoice(data);
        setForm(Object.fromEntries(FIELDS.map((f) => [f.key, data[f.key] ?? ""])));
        setLineItems(data.line_items ?? []);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleFieldChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const payload = { ...form };
      // Convert numeric fields back to numbers or null
      ["subtotal", "tax_amount", "total_amount"].forEach((k) => {
        payload[k] = payload[k] !== "" ? parseFloat(payload[k]) : null;
      });
      // Remove empty strings -> null
      Object.keys(payload).forEach((k) => {
        if (payload[k] === "") payload[k] = null;
      });
      const sanitisedItems = lineItems.map((li) => ({
        description: li.description || null,
        quantity:    li.quantity !== "" && li.quantity != null ? parseFloat(li.quantity) : null,
        unit_price:  li.unit_price !== "" && li.unit_price != null ? parseFloat(li.unit_price) : null,
        line_total:  li.line_total !== "" && li.line_total != null ? parseFloat(li.line_total) : null,
      }));
      payload.line_items = sanitisedItems;
      const updated = await updateInvoice(id, payload);
      setInvoice(updated);
      setLineItems(updated.line_items ?? []);
      setEditing(false);
      setSaved(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const cancelEdit = () => {
    setForm(Object.fromEntries(FIELDS.map((f) => [f.key, invoice[f.key] ?? ""])));
    setLineItems(invoice.line_items ?? []);
    setEditing(false);
    setError(null);
  };

  if (loading) return <div className="spinner-wrapper"><div className="spinner" /></div>;
  if (!invoice && error) return <div className="alert alert-error">{error}</div>;
  if (!invoice) return null;

  return (
    <>
      <div className="page-header flex-between">
        <div>
          <div className="flex-row" style={{ marginBottom: 4 }}>
            <button className="btn btn-secondary btn-sm" onClick={() => navigate(-1)}>
              &larr; Back
            </button>
            <h1 style={{ margin: 0 }}>Invoice #{invoice.id}</h1>
            <StatusBadge status={invoice.status} />
          </div>
          <p className="text-muted">{invoice.filename}</p>
        </div>
        <div className="flex-row">
          {!editing ? (
            <button className="btn btn-primary btn-sm" onClick={() => setEditing(true)}>
              Edit
            </button>
          ) : (
            <>
              <button className="btn btn-primary btn-sm" onClick={handleSave} disabled={saving}>
                {saving ? "Saving..." : "Save Changes"}
              </button>
              <button className="btn btn-secondary btn-sm" onClick={cancelEdit} disabled={saving}>
                Cancel
              </button>
            </>
          )}
        </div>
      </div>

      {error  && <div className="alert alert-error">{error}</div>}
      {saved  && <div className="alert alert-success">Invoice updated successfully.</div>}

      {invoice.validation_notes && (
        <div className="validation-notes">
          <strong>Validation notes:</strong> {invoice.validation_notes}
        </div>
      )}

      {/* Header fields */}
      <div className="card">
        <div className="card-title">Invoice Details</div>
        {editing ? (
          <div className="form-row">
            {FIELDS.map((f) => (
              <div className="form-group" key={f.key}>
                <label>{f.label}</label>
                <input
                  className="form-control"
                  type={f.type}
                  step="any"
                  value={form[f.key]}
                  onChange={(e) => handleFieldChange(f.key, e.target.value)}
                />
              </div>
            ))}
          </div>
        ) : (
          <div className="detail-grid">
            {FIELDS.map((f) => (
              <div className="detail-field" key={f.key}>
                <label>{f.label}</label>
                <div className="value">
                  {invoice[f.key] != null ? String(invoice[f.key]) : <span className="text-muted">Not extracted</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Line items */}
      <div className="card">
        <div className="card-title">Line Items</div>
        <LineItemsTable
          items={lineItems}
          readOnly={!editing}
          onChange={setLineItems}
        />
      </div>

      {/* Ask AI */}
      <div className="card">
        <div className="card-title">Ask AI about this invoice</div>
        <div className="ai-search-box">
          <input
            className="form-control ai-search-input"
            type="text"
            placeholder='e.g. "What is the total amount?" or "List all line items"'
            value={qaQuestion}
            onChange={(e) => setQaQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAsk()}
            disabled={qaLoading}
          />
          <button
            className="btn btn-primary"
            onClick={handleAsk}
            disabled={qaLoading || !qaQuestion.trim()}
          >
            {qaLoading ? "Thinking…" : "Ask AI"}
          </button>
        </div>

        {qaError && (
          <div className="alert alert-error" style={{ marginTop: 12 }}>
            {qaError.includes("not installed") || qaError.includes("not set")
              ? "AI not configured — set LLM_API_KEY in .env and run: pip install anthropic"
              : qaError}
          </div>
        )}
        {qaAnswer && (
          <div className="ai-answer">
            <div className="ai-answer-label">Answer</div>
            <div className="ai-answer-text">{qaAnswer}</div>
          </div>
        )}
      </div>

      {/* Raw OCR text (collapsible) */}
      {invoice.raw_text && (
        <div className="card">
          <div className="flex-between" style={{ marginBottom: showRaw ? 12 : 0 }}>
            <div className="card-title" style={{ marginBottom: 0 }}>Raw OCR Text</div>
            <button className="btn btn-secondary btn-sm" onClick={() => setShowRaw((s) => !s)}>
              {showRaw ? "Hide" : "Show"}
            </button>
          </div>
          {showRaw && (
            <pre style={{
              background: "#f8fafc",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-sm)",
              padding: "14px",
              fontSize: "12.5px",
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
              maxHeight: "400px",
              overflowY: "auto",
              marginTop: 12,
            }}>
              {invoice.raw_text}
            </pre>
          )}
        </div>
      )}
    </>
  );
}
