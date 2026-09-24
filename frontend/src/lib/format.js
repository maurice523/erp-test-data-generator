export function formatValue(value) {
  if (value === null || value === undefined || value === "") {
    return "";
  }
  return String(value);
}

export function orderLabel(order, index) {
  return order?.poNumber || order?.externalRefNo || `Generated ${index + 1}`;
}

export function getLineType(line) {
  return line?.configuration?.type || "";
}
