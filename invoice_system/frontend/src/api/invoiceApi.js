/**
 * Thin API client that wraps all calls to the FastAPI backend.
 * The Vite dev server proxies /api/* to http://127.0.0.1:8000.
 */

const BASE = "/api";

async function request(method, path, body = null) {
  const opts = {
    method,
    headers: body instanceof FormData ? {} : { "Content-Type": "application/json" },
    body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
  };
  const res = await fetch(`${BASE}${path}`, opts);
  if (!res.ok) {
    const text = await res.text();
    let detail = text;
    try {
      detail = JSON.parse(text)?.detail ?? text;
    } catch (_) {}
    throw new Error(detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/** Upload one or more File objects; returns UploadResponse. */
export function uploadInvoices(files) {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  return request("POST", "/invoices/upload", form);
}

/** Return paginated invoice list. */
export function listInvoices(skip = 0, limit = 100) {
  return request("GET", `/invoices?skip=${skip}&limit=${limit}`);
}

/** Return full invoice detail including line items. */
export function getInvoice(id) {
  return request("GET", `/invoices/${id}`);
}

/** Patch invoice header fields and/or line items. */
export function updateInvoice(id, payload) {
  return request("PUT", `/invoices/${id}`, payload);
}

/** Simple health probe. */
export function healthCheck() {
  return request("GET", "/health");
}

/** Search invoices by natural language query (no API key needed). */
export function searchInvoices(query) {
  return request("GET", `/ai/search?q=${encodeURIComponent(query)}`);
}

/** Ask a question about a specific invoice (requires LLM_API_KEY in .env). */
export function qaInvoice(invoiceId, question) {
  return request("POST", "/ai/qa", { invoice_id: invoiceId, question });
}
