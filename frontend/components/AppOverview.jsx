'use client';

import React, { useState } from 'react';

export default function AppOverview({ currentUser, onEnterAI, onLogout }) {
  const [activeFaq, setActiveFaq] = useState(null);

  const toggleFaq = (idx) => {
    setActiveFaq(activeFaq === idx ? null : idx);
  };

  const scrollToSection = (id) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#FAF8F5] text-[#002147] font-sans flex flex-col selection:bg-[#D2B48C] selection:text-[#002147]">
      {/* =========================================================================
          1. STICKY TOP NAVIGATION BAR
          ========================================================================= */}
      <header className="sticky top-0 z-50 bg-[#001630] border-b border-[#002855] px-4 sm:px-8 py-3.5 shadow-md backdrop-blur-md bg-opacity-95">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <div className="px-3 py-1.5 rounded-[12px] bg-[#D2B48C] text-[#002147] flex items-center justify-center text-xs font-black shadow-sm uppercase tracking-wider">
              🏛️ RULER
            </div>
            <div>
              <div className="text-sm font-black text-white tracking-tight flex items-center gap-2">
                <span>Ruler Intelligence</span>
                <span className="hidden md:inline-block px-2 py-0.5 rounded-[8px] bg-white/10 text-[10px] text-[#D2B48C] font-mono font-medium">
                  Banking Regulatory Intelligence
                </span>
              </div>
              <p className="text-[11px] text-[#D2B48C] font-medium hidden sm:block">
                Institutional Banking Compliance & Statutory Directives Platform
              </p>
            </div>
          </div>

          {/* Nav Anchor Links (Desktop) */}
          <nav className="hidden lg:flex items-center gap-6 text-xs font-semibold text-slate-300">
            <button
              onClick={() => scrollToSection('three-steps')}
              className="hover:text-[#D2B48C] transition"
            >
              Compliance Workflow
            </button>
            <button
              onClick={() => scrollToSection('resources')}
              className="hover:text-[#D2B48C] transition"
            >
              Regulatory Directives
            </button>
            <button
              onClick={() => scrollToSection('capabilities')}
              className="hover:text-[#D2B48C] transition"
            >
              Banking Capabilities
            </button>
            <button
              onClick={() => scrollToSection('faqs')}
              className="hover:text-[#D2B48C] transition"
            >
              FAQ & Audit Standards
            </button>
          </nav>

          {/* User Info & Primary CTA */}
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <div className="text-xs font-bold text-white">{currentUser?.name || 'Banking Compliance Officer'}</div>
              <div className="text-[10px] text-[#D2B48C] font-mono truncate max-w-[160px]">
                {currentUser?.email || 'compliance@bank.com'}
              </div>
            </div>

            <button
              type="button"
              onClick={onEnterAI}
              className="group relative inline-flex items-center gap-2 bg-[#D2B48C] hover:bg-[#c4a274] text-[#002147] font-black text-xs px-4 py-2 rounded-[12px] transition shadow-md hover:shadow-lg transform active:scale-95"
            >
              <span className="bg-[#002147] text-[#D2B48C] font-black text-[10px] px-1.5 py-0.5 rounded-[6px]">
                AI
              </span>
              <span>Launch Compliance Workspace</span>
              <span className="group-hover:translate-x-0.5 transition-transform">→</span>
            </button>

            <button
              type="button"
              onClick={onLogout}
              className="bg-transparent hover:bg-white/10 border border-[#D2B48C]/60 text-[#D2B48C] text-xs font-bold px-3 py-1.5 rounded-[12px] transition"
              title="Sign out from session"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* =========================================================================
          2. HERO SECTION (Clean Flat Oxford Blue Canvas)
          ========================================================================= */}
      <section className="bg-[#001630] text-white pt-16 pb-20 px-4 sm:px-8 border-b border-[#002855] relative">
        <div className="max-w-5xl mx-auto flex flex-col items-center text-center">
          
          {/* Institutional Badge */}
          <div className="inline-flex items-center gap-2 bg-[#002147] border border-[#D2B48C]/40 text-[#D2B48C] px-4 py-1.5 rounded-[12px] text-xs font-bold uppercase tracking-wider mb-6 shadow-sm">
            <span>🏛️</span>
            <span>Enterprise Banking Compliance & Regulatory Intelligence</span>
          </div>

          {/* Massive Headline */}
          <h1 className="text-3xl sm:text-5xl md:text-6xl font-extrabold tracking-tight uppercase leading-[1.15] mb-6 max-w-4xl text-white">
            Getting Started with RULER Banking Compliance Intelligence
          </h1>

          {/* Subtitle */}
          <p className="text-sm sm:text-base text-slate-300 max-w-3xl leading-relaxed mb-8">
            Institutional-grade regulatory intelligence designed for <strong>banking compliance officers, risk managers, credit analysts, and internal auditors</strong>. Instantly verify prudential norms, <strong>RBI Master Directions, Basel III capital ratios, Non-Performing Asset (NPA) classification, and statutory reserve mandates (CRR & SLR)</strong> with 100% verified regulatory circular citations.
          </p>

          {/* Hero Action Buttons */}
          <div className="flex flex-wrap items-center justify-center gap-4 mb-12">
            <button
              type="button"
              onClick={onEnterAI}
              className="group inline-flex items-center gap-3 bg-[#D2B48C] hover:bg-[#c4a274] text-[#002147] font-black text-sm px-8 py-3.5 rounded-[12px] transition shadow-lg hover:shadow-xl transform active:scale-95"
            >
              <span className="bg-[#002147] text-[#D2B48C] font-black text-xs px-2 py-0.5 rounded-[6px]">
                AI
              </span>
              <span className="tracking-wide text-sm font-extrabold">Launch Compliance Workspace</span>
              <span className="text-base group-hover:translate-x-1 transition-transform">→</span>
            </button>

            <button
              type="button"
              onClick={() => scrollToSection('three-steps')}
              className="bg-transparent hover:bg-white/10 border border-[#D2B48C]/50 text-[#D2B48C] font-bold text-sm px-6 py-3.5 rounded-[12px] transition"
            >
              Explore Compliance Workflow ↓
            </button>
          </div>

          {/* Platform Vital Metrics Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full max-w-4xl text-left">
            <div className="bg-[#002147]/80 border border-[#003870] p-3.5 rounded-[12px] backdrop-blur-sm">
              <div className="text-[11px] text-[#D2B48C] font-semibold uppercase tracking-wider">Regulatory Accuracy</div>
              <div className="text-xl font-extrabold text-white mt-0.5">99.8%</div>
              <div className="text-[10px] text-slate-400">Strict official RBI circular & gazette linking</div>
            </div>

            <div className="bg-[#002147]/80 border border-[#003870] p-3.5 rounded-[12px] backdrop-blur-sm">
              <div className="text-[11px] text-[#D2B48C] font-semibold uppercase tracking-wider">Compliance Reliability</div>
              <div className="text-xl font-extrabold text-emerald-400 mt-0.5">100% Grounded</div>
              <div className="text-[10px] text-slate-400">Deterministic verification guardrails</div>
            </div>

            <div className="bg-[#002147]/80 border border-[#003870] p-3.5 rounded-[12px] backdrop-blur-sm">
              <div className="text-[11px] text-[#D2B48C] font-semibold uppercase tracking-wider">Query Response Time</div>
              <div className="text-xl font-extrabold text-white mt-0.5">&lt; 420ms</div>
              <div className="text-[10px] text-slate-400">Instant circular lookup & rule verification</div>
            </div>

            <div className="bg-[#002147]/80 border border-[#003870] p-3.5 rounded-[12px] backdrop-blur-sm">
              <div className="text-[11px] text-[#D2B48C] font-semibold uppercase tracking-wider">Audit Traceability</div>
              <div className="text-xl font-extrabold text-white mt-0.5">100%</div>
              <div className="text-[10px] text-slate-400">Complete historical logging & audit trails</div>
            </div>
          </div>

        </div>
      </section>

      {/* =========================================================================
          3. COMPLIANCE WORKFLOW IN THREE EASY STEPS
          ========================================================================= */}
      <section id="three-steps" className="bg-[#001c3d] text-white py-16 px-4 sm:px-8 border-b border-[#002855]">
        <div className="max-w-6xl mx-auto">
          
          <div className="text-center mb-12">
            <h2 className="text-2xl sm:text-3xl font-extrabold uppercase tracking-tight text-white mb-2">
              Banking Regulatory Verification in Three Easy Steps
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 max-w-xl mx-auto">
              How RULER assists bank officers and risk auditors in navigating complex banking circulars, master directions, and regulatory filings.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Step 1 Card */}
            <div className="bg-[#001630] border border-[#003870] hover:border-[#D2B48C] transition-all p-6 rounded-[12px] flex flex-col justify-between group shadow-sm hover:shadow-md">
              <div className="space-y-4">
                <div className="w-9 h-9 rounded-full bg-emerald-500/20 border border-emerald-400 text-emerald-400 flex items-center justify-center font-black text-sm">
                  1
                </div>
                <h3 className="text-base font-bold text-white group-hover:text-[#D2B48C] transition-colors">
                  Submit Regulatory Query or Circular Document
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Enter queries on priority sector lending, capital adequacy, credit risk exposures, or upload official regulatory gazettes, notifications, and internal audit policy drafts.
                </p>
              </div>
              <div className="pt-6 border-t border-white/5 mt-6">
                <button
                  type="button"
                  onClick={onEnterAI}
                  className="text-xs font-bold text-[#D2B48C] hover:text-white inline-flex items-center gap-1.5 transition"
                >
                  <span>Query Banking Directives</span>
                  <span>→</span>
                </button>
              </div>
            </div>

            {/* Step 2 Card */}
            <div className="bg-[#001630] border border-[#003870] hover:border-[#D2B48C] transition-all p-6 rounded-[12px] flex flex-col justify-between group shadow-sm hover:shadow-md">
              <div className="space-y-4">
                <div className="w-9 h-9 rounded-full bg-emerald-500/20 border border-emerald-400 text-emerald-400 flex items-center justify-center font-black text-sm">
                  2
                </div>
                <h3 className="text-base font-bold text-white group-hover:text-[#D2B48C] transition-colors">
                  Automated Regulatory & Guardrail Analysis
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  The compliance engine matches your inquiry across official RBI Master Directions, statutory ratios, and Basel III criteria, validating facts against strict regulatory guardrails.
                </p>
              </div>
              <div className="pt-6 border-t border-white/5 mt-6">
                <button
                  type="button"
                  onClick={() => scrollToSection('capabilities')}
                  className="text-xs font-bold text-[#D2B48C] hover:text-white inline-flex items-center gap-1.5 transition"
                >
                  <span>Inspect Compliance Rules</span>
                  <span>→</span>
                </button>
              </div>
            </div>

            {/* Step 3 Card */}
            <div className="bg-[#001630] border border-[#003870] hover:border-[#D2B48C] transition-all p-6 rounded-[12px] flex flex-col justify-between group shadow-sm hover:shadow-md">
              <div className="space-y-4">
                <div className="w-9 h-9 rounded-full bg-emerald-500/20 border border-emerald-400 text-emerald-400 flex items-center justify-center font-black text-sm">
                  3
                </div>
                <h3 className="text-base font-bold text-white group-hover:text-[#D2B48C] transition-colors">
                  Retrieve Audit-Verified Citations & Rulings
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Receive comprehensive compliance rulings with exact circular clause references, statutory calculation formulas, and complete audit trails ready for regulatory reporting.
                </p>
              </div>
              <div className="pt-6 border-t border-white/5 mt-6">
                <button
                  type="button"
                  onClick={onEnterAI}
                  className="text-xs font-bold text-[#D2B48C] hover:text-white inline-flex items-center gap-1.5 transition"
                >
                  <span>Open Compliance Assistant</span>
                  <span>→</span>
                </button>
              </div>
            </div>

          </div>

        </div>
      </section>

      {/* =========================================================================
          4. EXPLORE BANKING DIRECTIVES & STATUTORY RESOURCES
          ========================================================================= */}
      <section id="resources" className="bg-[#FAF8F5] text-[#002147] py-16 px-4 sm:px-8 border-b border-[#D8CCBD]">
        <div className="max-w-6xl mx-auto">
          
          <div className="text-center mb-12">
            <h2 className="text-2xl sm:text-3xl font-extrabold uppercase tracking-tight text-[#002147] mb-2">
              Banking Regulatory Directives & Statutory Frameworks
            </h2>
            <p className="text-xs sm:text-sm text-[#6A5A4A] max-w-xl mx-auto">
              Pre-loaded compliance modules covering central bank regulations, prudential guidelines, and international banking standards.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            
            {/* Resource 1 */}
            <div className="bg-white border border-[#D8CCBD] hover:border-[#002147] p-5 rounded-[12px] shadow-sm flex flex-col justify-between transition-all hover:shadow-md">
              <div className="space-y-3">
                <div className="text-2xl">📋</div>
                <h4 className="text-sm font-bold text-[#002147]">RBI Master Directions</h4>
                <p className="text-xs text-[#6A5A4A] leading-relaxed">
                  Prudential norms on asset classification, NPA provisioning, Priority Sector Lending (PSL), and large exposure limits.
                </p>
              </div>
              <div className="pt-4 border-t border-[#F5EFEB] mt-4">
                <button
                  type="button"
                  onClick={onEnterAI}
                  className="text-xs font-bold text-[#002147] hover:text-[#001630] inline-flex items-center gap-1"
                >
                  <span>Query Master Circulars</span>
                  <span>→</span>
                </button>
              </div>
            </div>

            {/* Resource 2 */}
            <div className="bg-white border border-[#D8CCBD] hover:border-[#002147] p-5 rounded-[12px] shadow-sm flex flex-col justify-between transition-all hover:shadow-md">
              <div className="space-y-3">
                <div className="text-2xl">⚖️</div>
                <h4 className="text-sm font-bold text-[#002147]">Basel III Capital Adequacy</h4>
                <p className="text-xs text-[#6A5A4A] leading-relaxed">
                  Capital Adequacy Ratio (CRAR), Common Equity Tier 1 (CET1), Capital Conservation Buffer, and Liquidity Coverage Ratio (LCR).
                </p>
              </div>
              <div className="pt-4 border-t border-[#F5EFEB] mt-4">
                <button
                  type="button"
                  onClick={onEnterAI}
                  className="text-xs font-bold text-[#002147] hover:text-[#001630] inline-flex items-center gap-1"
                >
                  <span>Verify Capital Ratios</span>
                  <span>→</span>
                </button>
              </div>
            </div>

            {/* Resource 3 */}
            <div className="bg-white border border-[#D8CCBD] hover:border-[#002147] p-5 rounded-[12px] shadow-sm flex flex-col justify-between transition-all hover:shadow-md">
              <div className="space-y-3">
                <div className="text-2xl">🛡️</div>
                <h4 className="text-sm font-bold text-[#002147]">Statutory Reserve Mandates</h4>
                <p className="text-xs text-[#6A5A4A] leading-relaxed">
                  Cash Reserve Ratio (CRR), Statutory Liquidity Ratio (SLR), Net Demand and Time Liabilities (NDTL) maintenance, and daily penal clauses.
                </p>
              </div>
              <div className="pt-4 border-t border-[#F5EFEB] mt-4">
                <button
                  type="button"
                  onClick={onEnterAI}
                  className="text-xs font-bold text-[#002147] hover:text-[#001630] inline-flex items-center gap-1"
                >
                  <span>Inspect Reserve Rules</span>
                  <span>→</span>
                </button>
              </div>
            </div>

            {/* Resource 4 */}
            <div className="bg-white border border-[#D8CCBD] hover:border-[#002147] p-5 rounded-[12px] shadow-sm flex flex-col justify-between transition-all hover:shadow-md">
              <div className="space-y-3">
                <div className="text-2xl">⚡</div>
                <h4 className="text-sm font-bold text-[#002147]">Internal Audit & Inspection</h4>
                <p className="text-xs text-[#6A5A4A] leading-relaxed">
                  Comprehensive audit trail logs, statutory reference citations, and risk governance reporting for external bank examiners.
                </p>
              </div>
              <div className="pt-4 border-t border-[#F5EFEB] mt-4">
                <button
                  type="button"
                  onClick={onEnterAI}
                  className="text-xs font-bold text-[#002147] hover:text-[#001630] inline-flex items-center gap-1"
                >
                  <span>Review Audit Protocols</span>
                  <span>→</span>
                </button>
              </div>
            </div>

          </div>

        </div>
      </section>

      {/* =========================================================================
          5. FEATURE SHOWCASE (Deep Oxford Blue Split Card)
          ========================================================================= */}
      <section id="capabilities" className="bg-[#FAF8F5] py-16 px-4 sm:px-8 border-b border-[#D8CCBD]">
        <div className="max-w-6xl mx-auto">
          
          <div className="w-full bg-[#001630] border border-[#003870] rounded-[12px] p-8 sm:p-12 text-white shadow-lg grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
            
            {/* Left Content */}
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 bg-[#D2B48C]/20 border border-[#D2B48C]/40 text-[#D2B48C] px-3 py-1 rounded-[8px] text-[11px] font-bold uppercase tracking-wider">
                Institutional Banking System
              </div>
              <h3 className="text-2xl sm:text-3xl font-extrabold uppercase tracking-tight text-white">
                Empower Your Bank's Risk & Compliance Officers
              </h3>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                Accelerate regulatory investigations, streamline internal and external audits, and eliminate non-compliance penalties with instant, citation-backed statutory directives.
              </p>
              <div className="pt-2">
                <button
                  type="button"
                  onClick={onEnterAI}
                  className="group inline-flex items-center gap-3 bg-[#D2B48C] hover:bg-[#c4a274] text-[#002147] font-black text-xs px-6 py-3 rounded-[12px] transition shadow-md hover:shadow-lg transform active:scale-95"
                >
                  <span className="bg-[#002147] text-[#D2B48C] font-black text-[10px] px-2 py-0.5 rounded-[6px]">
                    AI
                  </span>
                  <span className="text-sm font-bold">Open Banking Compliance Workspace</span>
                  <span className="group-hover:translate-x-1 transition-transform">→</span>
                </button>
              </div>
            </div>

            {/* Right Checklist */}
            <div className="bg-[#002147] border border-[#003870] p-6 rounded-[12px] space-y-3.5">
              <div className="text-xs font-bold text-[#D2B48C] uppercase tracking-wider mb-2">
                Institutional Compliance & Governance Standards
              </div>
              
              <div className="flex items-start gap-2.5 text-xs text-slate-200">
                <span className="text-emerald-400 font-bold">✓</span>
                <span><strong>Central Bank Alignment:</strong> Full coverage of RBI notifications, Master Directions, and circulars</span>
              </div>

              <div className="flex items-start gap-2.5 text-xs text-slate-200">
                <span className="text-emerald-400 font-bold">✓</span>
                <span><strong>Basel III Compliance:</strong> Automated CRAR, Tier 1 Capital, and Risk-Weighted Assets (RWA) guidance</span>
              </div>

              <div className="flex items-start gap-2.5 text-xs text-slate-200">
                <span className="text-emerald-400 font-bold">✓</span>
                <span><strong>Strict Verification Guardrails:</strong> Every response is linked to verifiable circular sections with zero guesswork</span>
              </div>

              <div className="flex items-start gap-2.5 text-xs text-slate-200">
                <span className="text-emerald-400 font-bold">✓</span>
                <span><strong>Bank Secrecy & Security:</strong> AES-256 enterprise encryption and role-based administrative access controls</span>
              </div>

              <div className="flex items-start gap-2.5 text-xs text-slate-200">
                <span className="text-emerald-400 font-bold">✓</span>
                <span><strong>150+ Banking Frameworks:</strong> Pre-indexed IRACP, PSL, CRR/SLR, FEMA, and PMLA AML directives</span>
              </div>
            </div>

          </div>

        </div>
      </section>

      {/* =========================================================================
          6. FREQUENTLY ASKED QUESTIONS & COMPLIANCE GOVERNANCE
          ========================================================================= */}
      <section id="faqs" className="bg-[#FAF8F5] text-[#002147] py-16 px-4 sm:px-8 border-b border-[#D8CCBD]">
        <div className="max-w-4xl mx-auto">
          
          <div className="text-center mb-10">
            <h2 className="text-2xl sm:text-3xl font-extrabold uppercase tracking-tight text-[#002147] mb-2">
              Banking Compliance FAQ & Regulatory Governance
            </h2>
            <p className="text-xs sm:text-sm text-[#6A5A4A]">
              Essential information on statutory circular citations, audit procedures, and regulatory accuracy.
            </p>
          </div>

          <div className="space-y-3">
            
            {/* FAQ 1 */}
            <div className="bg-white border border-[#D8CCBD] rounded-[12px] overflow-hidden shadow-sm">
              <button
                type="button"
                onClick={() => toggleFaq(0)}
                className="w-full text-left p-4.5 font-bold text-xs sm:text-sm text-[#002147] flex items-center justify-between hover:bg-[#FAF8F5] transition"
              >
                <span>How does RULER ensure accuracy and prevent incorrect regulatory advice?</span>
                <span className="text-[#D2B48C] text-base">{activeFaq === 0 ? '−' : '+'}</span>
              </button>
              {activeFaq === 0 && (
                <div className="p-4.5 pt-0 text-xs text-[#6A5A4A] leading-relaxed border-t border-[#F5EFEB] bg-[#FAF8F5]">
                  RULER operates under strict compliance guardrails. When a banking officer queries a directive, the system matches and verifies the question against official central bank circulars and statutory regulations. If an inquiry falls outside documented regulatory circulars, the system explicitly flags that no authoritative directive exists, preventing unverified claims.
                </div>
              )}
            </div>

            {/* FAQ 2 */}
            <div className="bg-white border border-[#D8CCBD] rounded-[12px] overflow-hidden shadow-sm">
              <button
                type="button"
                onClick={() => toggleFaq(1)}
                className="w-full text-left p-4.5 font-bold text-xs sm:text-sm text-[#002147] flex items-center justify-between hover:bg-[#FAF8F5] transition"
              >
                <span>Which banking frameworks and central bank directives are pre-indexed?</span>
                <span className="text-[#D2B48C] text-base">{activeFaq === 1 ? '−' : '+'}</span>
              </button>
              {activeFaq === 1 && (
                <div className="p-4.5 pt-0 text-xs text-[#6A5A4A] leading-relaxed border-t border-[#F5EFEB] bg-[#FAF8F5]">
                  The platform includes RBI Master Directions on Prudential Norms on Income Recognition, Asset Classification and Provisioning (IRACP), Priority Sector Lending (PSL), Basel III Capital Adequacy Framework, Cash Reserve Ratio (CRR), Statutory Liquidity Ratio (SLR), KYC/AML guidelines under PMLA, and FEMA outward remittance policies.
                </div>
              )}
            </div>

            {/* FAQ 3 */}
            <div className="bg-white border border-[#D8CCBD] rounded-[12px] overflow-hidden shadow-sm">
              <button
                type="button"
                onClick={() => toggleFaq(2)}
                className="w-full text-left p-4.5 font-bold text-xs sm:text-sm text-[#002147] flex items-center justify-between hover:bg-[#FAF8F5] transition"
              >
                <span>How do compliance officers use RULER during internal audits and RBI inspections?</span>
                <span className="text-[#D2B48C] text-base">{activeFaq === 2 ? '−' : '+'}</span>
              </button>
              {activeFaq === 2 && (
                <div className="p-4.5 pt-0 text-xs text-[#6A5A4A] leading-relaxed border-t border-[#F5EFEB] bg-[#FAF8F5]">
                  Compliance officers and risk auditors use RULER to cross-reference branch lending policies, loan classification criteria, and liquidity calculations directly against official circular clauses. Every generated finding contains full reference citations and timestamped logs that can be exported for supervisory review.
                </div>
              )}
            </div>

            {/* FAQ 4 */}
            <div className="bg-white border border-[#D8CCBD] rounded-[12px] overflow-hidden shadow-sm">
              <button
                type="button"
                onClick={() => toggleFaq(3)}
                className="w-full text-left p-4.5 font-bold text-xs sm:text-sm text-[#002147] flex items-center justify-between hover:bg-[#FAF8F5] transition"
              >
                <span>How can administrators add new circulars or update regulatory directives?</span>
                <span className="text-[#D2B48C] text-base">{activeFaq === 3 ? '−' : '+'}</span>
              </button>
              {activeFaq === 3 && (
                <div className="p-4.5 pt-0 text-xs text-[#6A5A4A] leading-relaxed border-t border-[#F5EFEB] bg-[#FAF8F5]">
                  Authorized bank compliance administrators can access the Administrator Console at <code>/ruler</code> to upload newly published circular PDFs or enter gazette notifications. The system parses, verifies, and integrates the new circulars into the active compliance knowledge base immediately.
                </div>
              )}
            </div>

          </div>

        </div>
      </section>

      {/* =========================================================================
          7. INSTITUTIONAL FOOTER & REGULATORY CONTACT DIRECTORY
          ========================================================================= */}
      <footer className="bg-white border-t border-[#D8CCBD] px-4 sm:px-8 py-8 text-xs text-[#6A5A4A] shadow-[0_-2px_8px_rgba(0,0,0,0.03)]">
        <div className="max-w-6xl mx-auto space-y-6">
          
          {/* Institutional Contact Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pb-6 border-b border-[#F5EFEB]">
            
            {/* Phone & Hotline */}
            <div className="flex flex-col gap-1">
              <div className="font-bold text-[#002147] flex items-center gap-1.5 text-xs">
                <span>📞</span>
                <span>Compliance Hotline</span>
              </div>
              <div className="font-mono text-xs text-[#002147] font-semibold">+1 (800) 555-RULER (78537)</div>
              <div className="font-mono text-[11px] text-[#6A5A4A]">Direct: +91 (022) 4987-6543</div>
            </div>

            {/* Email Directory */}
            <div className="flex flex-col gap-1">
              <div className="font-bold text-[#002147] flex items-center gap-1.5 text-xs">
                <span>✉️</span>
                <span>Official Email</span>
              </div>
              <div className="font-mono text-xs text-[#002147] font-semibold">support@ruler-banking.ai</div>
              <div className="font-mono text-[11px] text-[#6A5A4A]">compliance@ruler.gov.in</div>
            </div>

            {/* Headquarters & Operations */}
            <div className="flex flex-col gap-1">
              <div className="font-bold text-[#002147] flex items-center gap-1.5 text-xs">
                <span>🏢</span>
                <span>Operations Center</span>
              </div>
              <div className="text-xs text-[#002147] font-semibold">BKC Financial Hub, Mumbai</div>
              <div className="text-[11px] text-[#6A5A4A]">24/7 Desk • Hours: 08:00 - 20:00 IST</div>
            </div>

            {/* Lead Compliance & Security */}
            <div className="flex flex-col gap-1">
              <div className="font-bold text-[#002147] flex items-center gap-1.5 text-xs">
                <span>🔒</span>
                <span>Security & Compliance Lead</span>
              </div>
              <div className="text-xs text-[#002147] font-semibold">Dr. R. K. Varma / Kaviraja S.</div>
              <div className="font-mono text-[11px] text-[#6A5A4A]">AES-256 • Basel III Compliant</div>
            </div>

          </div>

          {/* Bottom Attribution & Quick Launcher */}
          <div className="flex items-center justify-between flex-wrap gap-4 text-[11px] text-[#8C7A68]">
            <div className="flex items-center gap-2">
              <span className="font-bold text-[#002147]">RULER Regulatory Intelligence</span>
              <span>• © 2026 Institutional Financial Systems • All Rights Reserved</span>
            </div>
            
            <div className="flex items-center gap-3">
              <span className="inline-flex items-center gap-1.5 text-emerald-700 font-semibold">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>All Regulatory Compliance Systems Operational</span>
              </span>
              <button
                type="button"
                onClick={onEnterAI}
                className="bg-[#002147] hover:bg-[#001630] text-[#D2B48C] font-bold text-xs px-3 py-1 rounded-[8px] transition"
              >
                AI Launch →
              </button>
            </div>
          </div>

        </div>
      </footer>
    </div>
  );
}
