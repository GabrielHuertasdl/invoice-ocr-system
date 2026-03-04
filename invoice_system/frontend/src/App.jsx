import React from "react";
import { Routes, Route, NavLink } from "react-router-dom";
import InvoiceList from "./pages/InvoiceList";
import UploadPage from "./pages/UploadPage";
import InvoiceDetail from "./pages/InvoiceDetail";

export default function App() {
  return (
    <div className="app-shell">
      <header className="top-nav">
        <span className="brand">Invoice Processing System</span>
        <nav>
          <NavLink to="/" end className={({ isActive }) => isActive ? "active" : ""}>
            Invoices
          </NavLink>
          <NavLink to="/upload" className={({ isActive }) => isActive ? "active" : ""}>
            Upload
          </NavLink>
        </nav>
      </header>

      <main className="page">
        <Routes>
          <Route path="/" element={<InvoiceList />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/invoices/:id" element={<InvoiceDetail />} />
        </Routes>
      </main>
    </div>
  );
}
