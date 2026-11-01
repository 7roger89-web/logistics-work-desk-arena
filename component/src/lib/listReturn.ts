/**
 * LOGI-255-RETURN-TO-LIST — the list context travels in the router's OWN
 * location state; no sessionStorage, no new store, no duplicate filter model.
 *
 * Why this exists at all: the shell runs a `MemoryRouter` (see App.tsx), so an
 * in-app navigation never creates a history entry and never changes the URL.
 * The browser's Back button therefore cannot restore `/lo-hang?q=…`, and the
 * detail screen used to have no way back at all. The smallest fix that keeps
 * the existing router is to hand the exact list location to the detail screen
 * through `location.state` and give the operator one explicit control that
 * returns to it.
 *
 * The value is deliberately left as the operator's own list URL string
 * (`pathname + search`), so q / status / period / from / to / archive are all
 * carried by the ONE mechanism the list already uses to hold them
 * (`useQueryParam` over the route's search params). Nothing is re-parsed here.
 */

/** Route prefix of the list screen. Detail is `/lo-hang/<id>`. */
const LIST_PATH = "/lo-hang";

/**
 * The list location a `/lo-hang` link should return to.
 *
 * Only a screen that is ITSELF the list (never a detail route, never another
 * screen) may be remembered; anything else falls back to the plain list so a
 * "return" can never bounce back into the record it was opened from.
 */
export function listReturnTarget(pathname: string, search: string): string {
  const current = `${pathname || ""}${search || ""}`;
  return isListLocation(current) ? current : LIST_PATH;
}

/** True for `/lo-hang` and `/lo-hang?...`; false for `/lo-hang/<id>` or anything else. */
export function isListLocation(value: string): boolean {
  if (typeof value !== "string") return false;
  if (value === LIST_PATH) return true;
  return value.startsWith(`${LIST_PATH}?`);
}

/**
 * The list location carried by a `location.state` payload, or the safe
 * fallback `"/lo-hang"` for a direct entry (deep link, Home card, Inbox,
 * Receivables, …) that never came from the list.
 */
export function listReturnFromState(state: unknown): string {
  if (state && typeof state === "object") {
    const remembered = (state as Record<string, unknown>).listReturn;
    if (typeof remembered === "string" && isListLocation(remembered)) return remembered;
  }
  return LIST_PATH;
}

/** The router-state payload a list link attaches for the detail screen. */
export function listReturnState(listReturn: string): { listReturn: string } | undefined {
  return isListLocation(listReturn) ? { listReturn } : undefined;
}
