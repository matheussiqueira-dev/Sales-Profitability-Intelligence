import type { Metadata } from "next";
import { Source_Sans_3, Source_Serif_4 } from "next/font/google";
import Link from "next/link";
import "./globals.css";

// Self-hosted at build time by next/font: no runtime request to a font CDN.
const serif = Source_Serif_4({
  subsets: ["latin"],
  weight: ["600"],
  variable: "--font-serif",
  display: "swap",
});
const sans = Source_Sans_3({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Sales Profitability Intelligence | Matheus Siqueira",
  description:
    "Rentabilidade por margem de contribuição: vendas, descontos, devoluções e custos em um case de Analytics Engineering com dados sintéticos.",
  robots: { index: false, follow: false },
  openGraph: {
    title: "Sales Profitability Intelligence",
    description: "Da receita à contribuição, com dados conciliados.",
    type: "website",
  },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className={`${serif.variable} ${sans.variable}`}>
      <body>
        <a className="skip-link" href="#content">
          Ir ao conteúdo
        </a>
        <header className="site-header">
          <Link className="brand" href="/">
            Sales Profitability<span>Intelligence</span>
          </Link>
          <nav aria-label="Navegação principal">
            <Link href="/#analysis">Análise</Link>
            <Link href="/methodology">Metodologia</Link>
            <a href="https://github.com/matheussiqueira-dev/Sales-Profitability-Intelligence">
              Repositório
            </a>
          </nav>
        </header>
        {children}
        <footer>
          <span>Matheus Siqueira, Analytics Engineering</span>
          <a href="https://www.matheussiqueira.dev">Conhecer o portfólio</a>
          <span>
            Dados fictícios. Contribuição não representa lucro líquido.
          </span>
        </footer>
      </body>
    </html>
  );
}
