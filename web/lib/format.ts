const MISSING = "—";
const currency = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  maximumFractionDigits: 0,
});
const compactNumber = new Intl.NumberFormat("pt-BR", {
  notation: "compact",
  maximumFractionDigits: 1,
});
const ratio = new Intl.NumberFormat("pt-BR", {
  style: "percent",
  maximumFractionDigits: 1,
});

/** Undefined ratios (e.g. margin over zero revenue) render as "—", never as 0%. */
function finite(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

export const money = (value: string | number | null | undefined) => {
  const number = finite(value);
  return number === null ? MISSING : currency.format(number);
};
export const compact = (value: number) => compactNumber.format(value);
export const percent = (value: string | number | null | undefined) => {
  const number = finite(value);
  return number === null ? MISSING : ratio.format(number);
};
