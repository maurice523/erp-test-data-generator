import { getSelectedTotals } from "../../lib/orders";

export function TotalsFooter({ orders }) {
  const totals = getSelectedTotals(orders);
  const stats = [
    ["Total orders", totals.totalOrders],
    ["Total lines", totals.totalLines],
    ["Total quantity", totals.totalQuantity],
  ];

  return (
    <section className="grid shrink-0 grid-cols-3 divide-x divide-slate-200 border-t border-slate-200 bg-slate-50">
      {stats.map(([label, value]) => (
        <div className="px-4 py-2.5" key={label}>
          <p className="text-xs text-slate-500">{label}</p>
          <p className="text-lg font-semibold text-slate-900 tabular-nums">
            {value.toLocaleString()}
          </p>
        </div>
      ))}
    </section>
  );
}
