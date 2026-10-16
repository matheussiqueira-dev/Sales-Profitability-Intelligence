/**
 * SVG chart colors. Recharts writes presentation attributes, where CSS custom
 * properties are not reliable, so these mirror the :root tokens in globals.css.
 */
export const chart = {
  revenue: "#2463a6",
  revenueSoft: "#cfdeee",
  margin: "#08745b",
  loss: "#bc3941",
  grid: "#e6ebef",
  reference: "#8a98a5",
  axis: "#526271",
} as const;
