# RULER — Dual Dashboard Architecture (Next.js & Tailwind CSS)

## 1. Project Overview & Vision

**RULER** (*Regulatory Understanding, Lexical Extraction, and Retrieval*) provides an enterprise-grade regulatory AI platform featuring two purpose-built dashboard environments:
1. **User Portal**: A focused, minimalist conversational workspace built strictly for banking officers and analysts.
2. **Admin Portal**: An administrative control center for document ingestion, knowledge base chunk inspection, system telemetry, and feedback auditing.

---

## 2. Technology Stack

- **Framework**: Next.js 14+ (App Router) & React 18
- **Styling**: Tailwind CSS v3 with curated dark fintech design tokens
- **Typography**: Google Fonts (`Plus Jakarta Sans` for UI, `JetBrains Mono` for telemetry & code)
- **Backend Service**: FastAPI Python REST API on `http://127.0.0.1:8000`
- **State Management**: React state hooks with `localStorage` persistence
- **API Proxying**: Next.js reverse proxy (`rewrites` in `next.config.js` forwarding `/api/*` to FastAPI)

---

## 3. Component Hierarchy

```
frontend/
├── app/
│   ├── layout.jsx            # Root layout with typography and Oxford Blue / Tan tokens
│   ├── page.jsx              # Main route (/) for User Portal and authentication
│   ├── ruler/
│   │   └── page.jsx          # Dedicated Admin route (/ruler) with Admin Passkey gateway
│   └── globals.css           # Global Tailwind CSS directives
├── components/
│   ├── AuthScreen.jsx        # Login & Sign Up screen with User auth and Admin Passkey tab
│   ├── UserDashboard.jsx     # Minimalist User Portal (Chat space, History, Feedback, Generated Tokens, Chunks, Sign out)
│   ├── AssistantChat.jsx     # Conversational chat space with per-turn token metrics & chunk citations
│   ├── AdminDashboard.jsx    # Administrative portal (Document ingestion, diagnostics, feedback analytics)
│   ├── Header.jsx            # Top bar component
│   └── Sidebar.jsx           # Side navigation component
├── lib/
│   └── api.js                # Fetch client for /api/query, /api/upload, /api/upload-text, and /api/config
├── next.config.js            # Next.js configuration & API reverse proxy
├── package.json              # Next.js, React, Tailwind CSS dependencies
└── tailwind.config.js        # Oxford Blue and Tan color palette
```

---

## 4. User Portal Specifications (Strict Minimalist Mode)

The **User Portal** is designed exclusively with the essential tools needed for regulatory inquiry, stripped of all developer and debug clutter:

1. **Chat Space (`AssistantChat.jsx`)**:
   - Clean, responsive conversation interface with suggested regulatory prompt chips.
   - Grounded compliance answers with high-contrast, legible typography.

2. **Per-Response Generated Token Counter**:
   - Every assistant response explicitly displays: **`⚡ XX tokens generated`** directly alongside the answer.

3. **Source Chunks & Chunk Numbers**:
   - Every answer displays the exact document chunk citations: **`📑 Chunk #X [doc_0_chunk_Y]`** with expandable source text previews.

4. **User Feedback**:
   - Instant inline **👍 Helpful** and **👎 Needs Revision** buttons with real-time feedback recording.

5. **Query History**:
   - Dedicated tab to review previous queries, answers, generated tokens, source chunks, and user feedback ratings.

6. **Sign Out Button**:
   - Fast, secure sign-out in the top navigation bar.

---

## 5. Admin Portal Specifications (`AdminDashboard.jsx`)

The **Admin Portal** provides exclusive system oversight, document ingestion authority, and user audit analytics:

1. **User Conversations & Timestamps**:
   - Full chronological feed of user queries, chatbot answers, and exact query submission timestamps (`🕒 Asked at: <time>`).
   - Query search bar and filter controls (`All`, `👍 Helpful`, `👎 Needs Revision`, `✏️ Notes`).

2. **User Feedback & Officer Notes Analytics**:
   - Live telemetry on user satisfaction rate (%) and total rated responses.
   - Dedicated inspection panel displaying officer compliance thoughts and contextual notes submitted during chat.

3. **Exclusive Document & Policy Ingestion Authority**:
   - Only administrators have access to ingest documents into the RAG knowledge base.
   - **Text Editor Paste Mode**: Direct drafting, categorization (`Institutional Regulation`, `Audit & Compliance Reports`, `Capital Adequacy & Basel Framework`, `AML / KYC Directives`, `Cybersecurity & Encryption Standard`, `Internal Risk Policy`), token chunking, and instant vector indexing.
   - **File Upload Mode**: Supports drag-and-drop / file selection for `.txt`, `.md`, `.pdf`, `.json`, `.csv` (up to 10MB).

4. **Knowledge Base Repository (`/api/documents`)**:
   - Live inventory of all indexed policies and audit documents, chunk counts, doc IDs, and vectorization status.

5. **Design System & Aesthetics**:
   - Color combination: **Oxford Blue (`#002147`)** and **Tan (`#D2B48C`)** with `#FAF8F5` background, `#F5EFEB` cards, `#D8CCBD` borders.
   - Strict **12px curved corner radius (`rounded-[12px]`)** across all buttons, inputs, tabs, and cards.
   - Flat, minimalist design with zero gradients and no neon colors.

---

## 6. Running the Application

1. **Start the FastAPI Backend**:
   ```bash
   python -m uvicorn src.server:app --host 127.0.0.1 --port 8000 --reload
   ```

2. **Start Next.js Development Server**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open in Browser**:
   Visit 👉 **`http://localhost:3000`**
