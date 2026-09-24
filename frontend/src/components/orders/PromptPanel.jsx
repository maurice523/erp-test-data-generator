import { Icon } from "../ui/Icon";
import { MessageBubble } from "../ui/MessageBubble";

export function PromptPanel({
  error,
  isLoading,
  lastPrompt,
  onPromptChange,
  orderCount,
  prompt,
}) {
  const statusMessage = isLoading
    ? "Generating orders..."
    : `${orderCount} generated order${orderCount === 1 ? "" : "s"} ready.`;

  return (
    <section className="flex min-w-0 flex-col rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="text-sm font-semibold text-slate-900">Generate orders</h2>
      <p className="mb-3 text-xs text-slate-500">
        Describe the orders you need in plain English.
      </p>
      <div className="mb-3 flex min-h-10 flex-col gap-1.5">
        {lastPrompt ? (
          <MessageBubble tone="user">{lastPrompt}</MessageBubble>
        ) : null}
        {isLoading || error || orderCount > 0 ? (
          <MessageBubble tone={error ? "error" : "system"}>
            {error || statusMessage}
          </MessageBubble>
        ) : null}
      </div>
      <div className="mt-auto flex items-end gap-2 rounded-lg border border-slate-300 bg-white p-2 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-100">
        <textarea
          className="max-h-32 min-h-14 flex-1 resize-y border-0 bg-transparent px-1 text-sm leading-5 text-slate-900 outline-none placeholder:text-slate-400 disabled:cursor-not-allowed disabled:text-slate-400"
          disabled={isLoading}
          onChange={(event) => onPromptChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              event.currentTarget.form.requestSubmit();
            }
          }}
          placeholder="e.g. 3 sample orders shipping UPS ground to the US"
          value={prompt}
        />
        <button
          className="flex h-9 items-center gap-1.5 rounded-md bg-blue-600 px-3.5 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isLoading}
          type="submit"
        >
          {isLoading ? "Generating" : "Generate"}
          {!isLoading && <Icon name="Send" />}
        </button>
      </div>
    </section>
  );
}
