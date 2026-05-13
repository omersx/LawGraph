# Legal AI Agent — Frontend

This is the React / Next.js frontend for the **Legal AI Agent**, a professional-grade platform for analyzing contract and business law disputes.

## Features

- **Real-Time Streaming (SSE)**: Connects to the FastAPI LangGraph backend to stream pipeline activity steps (`ActivityCard`) and incremental text generation (`LegalAnswer`).
- **Interactive Consultations**: Supports multi-turn dialogue. If the backend's Intake Analyzer determines critical facts are missing, the UI dynamically renders a `ClarificationBubble` to prompt the user for more information before proceeding.
- **Dynamic Legal UI**:
  - Automatically formats the detected legal domain and jurisdiction.
  - Renders a structured IRAC (Issue, Rule, Application, Conclusion) legal analysis.
  - Highlights the Likely Outcome.
  - Presents a structured `SourcesPanel` with strict tool-verified citations (fetching holdings and principles from CourtListener via the backend).
  - Displays a Confidence Score badge based on backend assessments.
- **Actionable Document Generation (New!)**:
  - The "Download Report" feature uses **jsPDF** for client-side PDF generation.
  - Instantly converts the final JSON legal output into a professional, multi-page, formatted A4 legal memo.
  - Features zero backend dependencies — no Python PDF libraries required.

## Tech Stack

- **Framework**: [Next.js](https://nextjs.org/) (App Router)
- **Styling**: Vanilla CSS (`globals.css`) using custom color palettes, glassmorphism, and responsive design.
- **Streaming**: `@microsoft/fetch-event-source` for robust Server-Sent Events (SSE) handling.
- **PDF Generation**: `jspdf`

## Getting Started

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Configure Environment**
   Ensure your `.env.local` is set up with the backend API URL:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Run the Development Server**
   ```bash
   npm run dev
   ```

Open [http://localhost:3000](http://localhost:3000) with your browser to access the Legal AI Agent interface.

## Architecture Notes

### Client-Side PDF Generation
The `generateLegalReport()` function (in `lib/generatePDF.js`) is dynamically imported when the user clicks "Download Report". This ensures the `jspdf` library doesn't bloat the initial page load. It takes the structured `finalOutput` JSON state and uses canvas-drawing commands to render a highly polished document including headers, IRAC formatting, citation tables, and a disclaimer footer.
