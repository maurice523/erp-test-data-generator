import { ACTIVE_NAVIGATION_ITEM, NAVIGATION_ITEMS } from "../../constants";
import { Icon } from "../ui/Icon";

export function LeftRail() {
  return (
    <aside className="hidden w-52 shrink-0 border-r border-slate-200 bg-white lg:block">
      <nav className="space-y-0.5 p-3">
        <p className="px-2 pb-2 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
          Modules
        </p>
        {NAVIGATION_ITEMS.map((item) => {
          const active = item === ACTIVE_NAVIGATION_ITEM;
          return (
            <div
              aria-current={active ? "page" : undefined}
              className={`flex cursor-default items-center gap-2.5 rounded-md px-2 py-1.5 text-sm ${
                active
                  ? "bg-blue-50 font-medium text-blue-700"
                  : "text-slate-500"
              }`}
              key={item}
            >
              <Icon name={item} />
              {item}
            </div>
          );
        })}
      </nav>
    </aside>
  );
}
