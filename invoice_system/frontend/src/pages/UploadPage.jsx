import React, { useCallback, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { uploadInvoices } from "../api/invoiceApi";
import StatusBadge from "../components/StatusBadge";

const ACCEPTED = ".pdf,.png,.jpg,.jpeg";

export default function UploadPage() {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [results, setResults]             = useState([]);
  const [uploading, setUploading]         = useState(false);
  const [dragOver, setDragOver]           = useState(false);
  const [error, setError]                 = useState(null);
  const inputRef = useRef(null);
  const navigate = useNavigate();

  const addFiles = (fileList) => {
    const arr = Array.from(fileList);
    setSelectedFiles((prev) => {
      const names = new Set(prev.map((f) => f.name));
      return [...prev, ...arr.filter((f) => !names.has(f.name))];
    });
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    addFiles(e.dataTransfer.files);
  }, []);

  const handleDragOver = (e) => { e.preventDefault(); setDragOver(true); };
  const handleDragLeave = () => setDragOver(false);

  const removeFile = (name) => {
    setSelectedFiles((prev) => prev.filter((f) => f.name !== name));
  };

  const handleSubmit = async () => {
    if (!selectedFiles.length) return;
    setUploading(true);
    setError(null);
    setResults([]);
    try {
      const resp = await uploadInvoices(selectedFiles);
      setResults(resp.results);
      setSelectedFiles([]);
    } catch (e) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <>
      <div className="page-header">
        <h1>Upload Invoices</h1>
        <p>Select one or more PDF or image files to process.</p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        <div
          className={`drop-zone${dragOver ? " drag-over" : ""}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => inputRef.current?.click()}
        >
          <div className="dz-icon">&#8679;</div>
          <p>
            <strong>Click to browse</strong> or drag and drop files here
          </p>
          <p style={{ marginTop: 6, fontSize: 12 }}>PDF, PNG, JPEG supported</p>
          <input
            ref={inputRef}
            type="file"
            multiple
            accept={ACCEPTED}
            style={{ display: "none" }}
            onChange={(e) => addFiles(e.target.files)}
          />
        </div>

        {selectedFiles.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <p style={{ fontWeight: 600, marginBottom: 8 }}>
              {selectedFiles.length} file(s) selected:
            </p>
            {selectedFiles.map((f) => (
              <div key={f.name} className="upload-result-item">
                <span className="filename">{f.name}</span>
                <span className="text-muted" style={{ fontSize: 12 }}>
                  {(f.size / 1024).toFixed(1)} KB
                </span>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={(e) => { e.stopPropagation(); removeFile(f.name); }}
                >
                  Remove
                </button>
              </div>
            ))}

            <div className="flex-row mt-4">
              <button
                className="btn btn-primary"
                onClick={handleSubmit}
                disabled={uploading}
              >
                {uploading ? "Processing..." : "Upload and Process"}
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => setSelectedFiles([])}
                disabled={uploading}
              >
                Clear
              </button>
            </div>
          </div>
        )}
      </div>

      {results.length > 0 && (
        <div className="card">
          <div className="card-title">Processing Results</div>
          <div className="upload-results">
            {results.map((r, i) => (
              <div key={i} className="upload-result-item">
                <span className="filename">{r.filename}</span>
                <StatusBadge status={r.status} />
                {r.invoice_id != null && (
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => navigate(`/invoices/${r.invoice_id}`)}
                  >
                    View
                  </button>
                )}
                {r.message && (
                  <span className="message">{r.message}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
