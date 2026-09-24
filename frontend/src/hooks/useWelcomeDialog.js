import { useState } from "react";

import { WELCOME_SEEN_KEY } from "../constants";
import { safeSessionGet, safeSessionSet } from "../lib/session";

// Shown once per browser session: a returning visitor sees it again, someone
// reloading the page does not.
export function useWelcomeDialog() {
  const [isOpen, setIsOpen] = useState(() => !safeSessionGet(WELCOME_SEEN_KEY));

  function dismiss() {
    safeSessionSet(WELCOME_SEEN_KEY, "true");
    setIsOpen(false);
  }

  function reopen() {
    setIsOpen(true);
  }

  return { dismiss, isOpen, reopen };
}
