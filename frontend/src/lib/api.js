const ORDER_GENERATOR_PATH = "/api/order-generator";

// FastAPI reports failures as {"detail": "..."}; show that text rather than
// the raw JSON the UI used to display.
async function readErrorMessage(response) {
  const body = await response.text();

  try {
    const parsed = JSON.parse(body);
    const detail = parsed?.detail;
    if (typeof detail === "string") return detail;
    if (detail) return JSON.stringify(detail);
  } catch {
    // Not JSON: fall through and use the raw body.
  }

  return body || `Request failed with ${response.status}`;
}

export async function requestOrders(text) {
  const params = new URLSearchParams({ text });
  const response = await fetch(`${ORDER_GENERATOR_PATH}?${params}`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  const data = await response.json();
  if (!Array.isArray(data)) {
    throw new Error("The API returned an unexpected order format.");
  }

  return data;
}
