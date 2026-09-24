import { orderLabel } from "../../lib/format";

export function OrderSelector({ orders, selectedIndex, onSelect }) {
  return (
    <div className="flex shrink-0 items-center gap-1.5 overflow-x-auto border-b border-slate-200 px-4 py-2.5">
      <span className="mr-1 text-xs font-medium text-slate-500">Orders</span>
      {orders.length === 0 ? (
        <span className="text-xs text-slate-400">
          None yet. Submit an order request above.
        </span>
      ) : (
        orders.map((order, index) => (
          <button
            className={`h-7 shrink-0 rounded-full border px-3 text-xs font-medium ${
              selectedIndex === index
                ? "border-blue-600 bg-blue-600 text-white"
                : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50"
            }`}
            key={`${orderLabel(order, index)}-${index}`}
            onClick={() => onSelect(index)}
            type="button"
          >
            {orderLabel(order, index)}
          </button>
        ))
      )}
    </div>
  );
}
