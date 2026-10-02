import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OferBus — Planejamento Operacional",
  description: "Workspace de planejamento da operação de transporte público urbano.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
