// Private browsing and blocked site data make sessionStorage throw, so a
// failure here just means the dialog shows again.
export function safeSessionGet(key) {
  try {
    return window.sessionStorage.getItem(key);
  } catch {
    return null;
  }
}

export function safeSessionSet(key, value) {
  try {
    window.sessionStorage.setItem(key, value);
  } catch {
    // Ignore: the dialog is a convenience, not something worth breaking over.
  }
}
