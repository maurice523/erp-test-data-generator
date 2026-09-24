import { orderLabel } from "../../lib/format";
import { OrderHeaderFields } from "./OrderHeaderFields";
import { PromptPanel } from "./PromptPanel";

// Wraps both halves of the request row in one <form> so the textarea's
// Enter-to-submit keeps working.
export function OrderRequestForm({
  error,
  isLoading,
  lastPrompt,
  onPromptChange,
  onSubmit,
  orderCount,
  prompt,
  selectedIndex,
  selectedOrder,
}) {
  return (
    <form className="shrink-0" onSubmit={onSubmit}>
      <div className="mb-4">
        <p className="text-xs text-slate-500">Sales / Sales Orders</p>
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-semibold text-slate-900">
            Sales Order
            {selectedOrder ? (
              <span className="font-normal text-slate-500">
                {" "}
                {orderLabel(selectedOrder, selectedIndex)}
              </span>
            ) : null}
          </h1>
          {selectedOrder ? (
            <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200">
              Generated
            </span>
          ) : null}
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(340px,440px)_1fr]">
        <PromptPanel
          error={error}
          isLoading={isLoading}
          lastPrompt={lastPrompt}
          onPromptChange={onPromptChange}
          orderCount={orderCount}
          prompt={prompt}
        />
        <OrderHeaderFields selectedOrder={selectedOrder} />
      </div>
    </form>
  );
}
