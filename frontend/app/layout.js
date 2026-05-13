import "./globals.css";

export const metadata = {
  title: "LawGraph — Contract & Business Law Intelligence",
  description:
    "AI-powered legal reasoning system for contract disputes, providing citation-backed analysis with real legal sources.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
