export function MessageBubble({ children, tone }) {
  const styles = {
    user: "ml-auto bg-blue-600 text-white",
    error: "mr-auto border border-red-200 bg-red-50 text-red-700",
    system: "mr-auto border border-slate-200 bg-white text-slate-600",
  };

  return (
    <div
      className={`max-w-[88%] rounded-lg px-3 py-1.5 text-sm leading-5 ${styles[tone]}`}
    >
      {children}
    </div>
  );
}
