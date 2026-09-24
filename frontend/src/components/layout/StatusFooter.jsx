export function StatusFooter({ error, isLoading, orders }) {
  const message = error
    ? error
    : isLoading
      ? "Generating orders..."
      : `${orders.length} generated order${orders.length === 1 ? "" : "s"} ready`;

  const dot = error
    ? "bg-red-500"
    : isLoading
      ? "bg-amber-400 animate-pulse"
      : "bg-emerald-500";

  return (
    <footer className="flex h-7 shrink-0 items-center gap-2 border-t border-slate-200 bg-white px-4 text-xs text-slate-500">
      <span className={`h-2 w-2 rounded-full ${dot}`} />
      <span className={error ? "text-red-600" : ""}>{message}</span>
      <span className="ml-auto hidden sm:inline">Sales · Demo environment</span>
    </footer>
  );
}
