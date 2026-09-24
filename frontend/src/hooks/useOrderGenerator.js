import { useState } from "react";

import { requestOrders } from "../lib/api";

const DEFAULT_TAB = "Lines";

export function useOrderGenerator() {
  const [orders, setOrders] = useState([]);
  const [lastPrompt, setLastPrompt] = useState("");
  const [selectedOrderIndex, setSelectedOrderIndex] = useState(0);
  const [activeTab, setActiveTab] = useState(DEFAULT_TAB);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function submit(text) {
    const trimmedPrompt = text.trim();
    if (!trimmedPrompt) {
      setError("Enter an order request.");
      return;
    }

    setIsLoading(true);
    setError("");
    setOrders([]);
    setSelectedOrderIndex(0);
    setLastPrompt(trimmedPrompt);

    try {
      const data = await requestOrders(trimmedPrompt);
      setOrders(data);
      setSelectedOrderIndex(0);
      setActiveTab(DEFAULT_TAB);
    } catch (requestError) {
      setError(requestError.message || "Failed to generate orders.");
    } finally {
      setIsLoading(false);
    }
  }

  return {
    activeTab,
    error,
    isLoading,
    lastPrompt,
    orders,
    selectedOrder: orders[selectedOrderIndex] ?? null,
    selectedOrderIndex,
    selectTab: setActiveTab,
    selectOrder: setSelectedOrderIndex,
    submit,
  };
}
