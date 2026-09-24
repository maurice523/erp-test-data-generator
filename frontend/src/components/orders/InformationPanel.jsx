import { formatValue } from "../../lib/format";
import { OrderLinesGrid } from "./OrderLinesGrid";

export function InformationPanel({ activeTab, selectedOrder, orders }) {
  const address = selectedOrder?.shipToAddress ?? {};

  if (activeTab === "Lines") {
    return <OrderLinesGrid selectedOrder={selectedOrder} />;
  }

  if (activeTab === "JSON") {
    return (
      <pre className="min-h-0 flex-1 overflow-auto bg-slate-50 p-4 font-mono text-xs leading-relaxed text-slate-700">
        {JSON.stringify(orders, null, 2)}
      </pre>
    );
  }

  const rows = {
    Shipping: [
      ["Ship-to name", address.address1],
      ["Address", address.address2],
      ["City", address.city],
      ["State / province", address.state],
      ["Postal code", address.zipCode],
      ["Country", address.countryCode],
    ],
    Details: [
      ["PO number", selectedOrder?.poNumber],
      ["External reference", selectedOrder?.externalRefNo],
      ["Contact", selectedOrder?.contact?.emailAddress],
      ["Attachments", selectedOrder?.attachments?.length ?? 0],
    ],
    History: [
      ["Created by", "Order Generator"],
      ["Status", selectedOrder ? "Generated" : ""],
      ["Source", selectedOrder ? "Simulated" : ""],
      ["Lines", selectedOrder?.lines?.length ?? 0],
    ],
  }[activeTab];

  return (
    <div className="min-h-0 flex-1 overflow-auto p-4">
      <dl className="grid max-w-3xl grid-cols-1 gap-x-8 md:grid-cols-2">
        {(rows ?? []).map(([label, value]) => (
          <div
            className="flex justify-between gap-4 border-b border-slate-100 py-2 text-sm"
            key={label}
          >
            <dt className="text-slate-500">{label}</dt>
            <dd className="truncate text-right font-medium text-slate-900">
              {formatValue(value) || "—"}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
