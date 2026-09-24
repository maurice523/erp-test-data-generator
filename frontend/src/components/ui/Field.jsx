export function Field({
  label,
  name,
  value,
  onChange,
  type = "text",
  readOnly = false,
  wide = false,
}) {
  return (
    <label className={`min-w-0 ${wide ? "col-span-2" : ""}`}>
      <span className="mb-1 block truncate text-xs font-medium text-slate-500">
        {label}
      </span>
      <input
        className={`h-8 w-full rounded-md border border-slate-300 px-2.5 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 ${
          readOnly ? "bg-slate-50" : "bg-white"
        }`}
        name={name}
        onChange={onChange}
        readOnly={readOnly}
        type={type}
        value={value}
      />
    </label>
  );
}
