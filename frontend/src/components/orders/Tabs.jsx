import { TABS } from "../../constants";

export function Tabs({ activeTab, onChange }) {
  return (
    <div className="flex shrink-0 gap-5 overflow-x-auto border-b border-slate-200 px-4">
      {TABS.map((tab) => (
        <button
          className={`-mb-px h-10 whitespace-nowrap border-b-2 text-sm ${
            activeTab === tab
              ? "border-blue-600 font-medium text-blue-700"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
          key={tab}
          onClick={() => onChange(tab)}
          type="button"
        >
          {tab}
        </button>
      ))}
    </div>
  );
}
