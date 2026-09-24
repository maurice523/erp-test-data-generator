import { formatValue, getLineType } from "../../lib/format";

const HEADERS = [
  ["Line", ""],
  ["Item number", ""],
  ["Description", ""],
  ["Line type", ""],
  ["Quantity", "text-right"],
  ["Review required", ""],
  ["Status", ""],
];

export function OrderLinesGrid({ selectedOrder }) {
  const lines = selectedOrder?.lines ?? [];

  return (
    <div className="min-h-0 flex-1 overflow-auto">
      <table className="w-full min-w-[820px] border-collapse text-sm">
        <thead className="sticky top-0 z-10 bg-slate-50">
          <tr className="border-b border-slate-200 text-left text-xs font-medium tracking-wide text-slate-500 uppercase">
            {HEADERS.map(([label, align]) => (
              <th className={`px-4 py-2.5 ${align}`} key={label}>
                {label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {lines.length === 0 ? (
            <tr>
              <td className="px-4 py-8 text-center text-slate-400" colSpan={HEADERS.length}>
                Generated order lines will appear here.
              </td>
            </tr>
          ) : (
            lines.map((line, index) => (
              <tr
                className="border-b border-slate-100 text-slate-700 hover:bg-slate-50"
                key={`${line.partNo}-${index}`}
              >
                <td className="px-4 py-2.5 text-slate-400 tabular-nums">
                  {index + 1}
                </td>
                <td className="px-4 py-2.5 font-medium text-slate-900">
                  {formatValue(line.partNo)}
                </td>
                <td className="max-w-[320px] truncate px-4 py-2.5">
                  Generated order line for {formatValue(line.partNo)}
                </td>
                <td className="px-4 py-2.5">{getLineType(line)}</td>
                <td className="px-4 py-2.5 text-right tabular-nums">
                  {formatValue(line.quantity)}
                </td>
                <td className="px-4 py-2.5">
                  {line.configuration?.proofRequested ? "Yes" : "No"}
                </td>
                <td className="px-4 py-2.5">
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                    Generated
                  </span>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
