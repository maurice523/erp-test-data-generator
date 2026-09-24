export const TABS = ["Lines", "Shipping", "Details", "History", "JSON"];

// Sidebar modules. Only "Sales Orders" is part of this demo; the rest are
// there so the screen reads like a full ERP.
export const NAVIGATION_ITEMS = [
  "Dashboard",
  "Sales Orders",
  "Customers",
  "Inventory",
  "Purchasing",
  "Shipping",
  "Invoicing",
  "Reports",
];

export const ACTIVE_NAVIGATION_ITEM = "Sales Orders";

export const EXAMPLE_PROMPTS = [
  "3 sample orders shipping UPS ground to the US",
  "2 no print orders to Canada with at least 4 lines each",
  "5 sample orders, quantities between 50 and 200",
  "orders shipping UPS Next Day Air to Canada",
];

export const WELCOME_SEEN_KEY = "orderGenerator.welcomeSeen";
