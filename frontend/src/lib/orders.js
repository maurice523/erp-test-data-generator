export function getSelectedTotals(orders) {
  const allLines = orders.flatMap((order) => order.lines ?? []);
  const totalQuantity = allLines.reduce(
    (sum, line) => sum + Number(line.quantity ?? 0),
    0,
  );

  return {
    totalOrders: orders.length,
    totalLines: allLines.length,
    totalQuantity,
  };
}
