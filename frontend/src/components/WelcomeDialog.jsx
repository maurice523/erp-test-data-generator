import { useEffect, useRef } from "react";

import { EXAMPLE_PROMPTS } from "../constants";

export function WelcomeDialog({ onClose, onUsePrompt, open }) {
  const dialogRef = useRef(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  return (
    <dialog
      aria-labelledby="welcome-title"
      className="m-auto w-[min(92vw,560px)] max-h-[85vh] overflow-y-auto rounded-lg border border-slate-200 bg-white p-0 text-slate-700 shadow-2xl backdrop:bg-slate-900/50"
      onClose={onClose}
      ref={dialogRef}
    >
      <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3">
        <h2 className="text-base font-semibold text-slate-900" id="welcome-title">
          About this demo
        </h2>
        <button
          aria-label="Close"
          className="rounded px-1.5 text-lg leading-none text-slate-400 hover:bg-slate-100 hover:text-slate-700"
          onClick={onClose}
          type="button"
        >
          &times;
        </button>
      </div>

      <div className="space-y-4 px-5 py-4 text-sm leading-6">
        <p>
          Describe the sales orders you need in plain English and this tool
          generates them for you. It reads order history from a PostgreSQL
          database, learns the patterns in it, and builds new orders that follow
          the same shape, which is useful for filling a test system with data
          that looks genuine.
        </p>
        <p>
          The screen is laid out like a typical ERP sales order page, so the
          generated orders appear the way they would in a real system.
        </p>

        <div>
          <h3 className="mb-2 text-xs font-semibold tracking-wider text-slate-500 uppercase">
            Try one of these
          </h3>
          <ul className="space-y-1.5">
            {EXAMPLE_PROMPTS.map((example) => (
              <li key={example}>
                <button
                  className="w-full rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-left text-sm hover:border-blue-300 hover:bg-blue-50"
                  onClick={() => onUsePrompt(example)}
                  type="button"
                >
                  {example}
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h3 className="mb-2 text-xs font-semibold tracking-wider text-slate-500 uppercase">
            What it understands
          </h3>
          <ul className="list-disc space-y-0.5 pl-5 text-sm text-slate-600">
            <li>Carrier, by name - "UPS ground", "FedEx"</li>
            <li>Order type - "sample" or "no print"</li>
            <li>Country - United States or Canada</li>
            <li>A specific order number</li>
            <li>How many orders, and the minimum lines per order</li>
            <li>Minimum and maximum quantity per line</li>
          </ul>
          <p className="mt-2 text-sm text-slate-500">
            Anything you leave out simply is not filtered on.
          </p>
        </div>
      </div>

      <div className="flex justify-end border-t border-slate-200 bg-slate-50 px-5 py-3">
        <button
          className="h-9 rounded-md bg-blue-600 px-4 text-sm font-medium text-white hover:bg-blue-700"
          onClick={onClose}
          type="button"
        >
          Start generating
        </button>
      </div>
    </dialog>
  );
}
