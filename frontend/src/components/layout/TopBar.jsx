import { Icon } from "../ui/Icon";

export function TopBar({ onHelp }) {
  return (
    <header className="flex h-12 shrink-0 items-center gap-4 bg-slate-900 px-4 text-white">
      <div className="flex items-center gap-2.5">
        <span className="grid h-7 w-7 place-items-center rounded-md bg-blue-600 text-[11px] font-bold tracking-wide">
          OM
        </span>
        <span className="text-sm font-semibold">Order Management</span>
      </div>

      <div className="hidden flex-1 justify-center md:flex">
        <label className="relative w-full max-w-md">
          <Icon
            className="pointer-events-none absolute top-1/2 left-2.5 h-4 w-4 -translate-y-1/2 text-slate-400"
            name="Search"
          />
          <input
            className="h-8 w-full cursor-not-allowed rounded-md border border-slate-700 bg-slate-800 pr-3 pl-8 text-sm text-slate-300 placeholder:text-slate-500 outline-none"
            disabled
            placeholder="Search orders, customers, items..."
            title="Not part of this demo"
          />
        </label>
      </div>

      <div className="ml-auto flex items-center gap-3">
        <button
          className="flex cursor-pointer items-center gap-1.5 rounded-md px-2 py-1 text-sm text-slate-300 hover:bg-slate-800 hover:text-white"
          onClick={onHelp}
          type="button"
        >
          <Icon name="Help" />
          About this demo
        </button>
        <span className="grid h-7 w-7 place-items-center rounded-full bg-slate-700 text-[11px] font-semibold">
          MN
        </span>
      </div>
    </header>
  );
}
