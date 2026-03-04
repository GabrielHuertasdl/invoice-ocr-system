import React from "react";

/**
 * Editable line items table.
 *
 * Props:
 *   items    - array of line item objects
 *   readOnly - if true, renders a plain display table (no editing controls)
 *   onChange - callback(newItems) called on any change
 */
export default function LineItemsTable({ items = [], readOnly = false, onChange }) {
  const handleChange = (index, field, value) => {
    const updated = items.map((item, i) =>
      i === index ? { ...item, [field]: value === "" ? null : value } : item
    );
    onChange(updated);
  };

  const addRow = () => {
    onChange([...items, { description: "", quantity: "", unit_price: "", line_total: "" }]);
  };

  const removeRow = (index) => {
    onChange(items.filter((_, i) => i !== index));
  };

  const numField = (val) => (val === null || val === undefined ? "" : val);

  return (
    <div>
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th style={{ width: "40%" }}>Description</th>
              <th>Quantity</th>
              <th>Unit Price</th>
              <th>Line Total</th>
              {!readOnly && <th style={{ width: "48px" }}></th>}
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr>
                <td colSpan={readOnly ? 4 : 5} className="text-muted" style={{ textAlign: "center", padding: "20px" }}>
                  No line items extracted.
                </td>
              </tr>
            )}
            {items.map((item, i) =>
              readOnly ? (
                <tr key={i}>
                  <td>{item.description ?? "-"}</td>
                  <td>{item.quantity ?? "-"}</td>
                  <td>{item.unit_price != null ? Number(item.unit_price).toFixed(2) : "-"}</td>
                  <td>{item.line_total != null ? Number(item.line_total).toFixed(2) : "-"}</td>
                </tr>
              ) : (
                <tr key={i}>
                  <td>
                    <input
                      className="form-control"
                      value={item.description ?? ""}
                      onChange={(e) => handleChange(i, "description", e.target.value)}
                    />
                  </td>
                  <td>
                    <input
                      className="form-control"
                      type="number"
                      step="any"
                      value={numField(item.quantity)}
                      onChange={(e) => handleChange(i, "quantity", e.target.value)}
                    />
                  </td>
                  <td>
                    <input
                      className="form-control"
                      type="number"
                      step="any"
                      value={numField(item.unit_price)}
                      onChange={(e) => handleChange(i, "unit_price", e.target.value)}
                    />
                  </td>
                  <td>
                    <input
                      className="form-control"
                      type="number"
                      step="any"
                      value={numField(item.line_total)}
                      onChange={(e) => handleChange(i, "line_total", e.target.value)}
                    />
                  </td>
                  <td>
                    <button className="btn btn-secondary btn-sm" onClick={() => removeRow(i)} title="Remove row">
                      X
                    </button>
                  </td>
                </tr>
              )
            )}
          </tbody>
        </table>
      </div>
      {!readOnly && (
        <button className="btn btn-secondary btn-sm mt-4" onClick={addRow}>
          + Add Row
        </button>
      )}
    </div>
  );
}
