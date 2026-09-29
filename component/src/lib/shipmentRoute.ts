/**
 * LOGI_SHIPMENT_SLASH_ROUTE_REPAIR_01 (Issue #138) — one shipment identity is
 * ONE route segment, even when the identity itself contains `/`.
 *
 * The route table exposes exactly one dynamic segment (`/lo-hang/:id`), and the
 * shipped react-router matcher compiles that parameter to `([^\/]+)`. A raw
 * concatenation of an identity such as `LO/LEGACY/001` therefore produced the
 * multi-segment pathname `/lo-hang/LO/LEGACY/001`, which matches no detail
 * route and falls through to the `*` wildcard → NotFound
 * ("Không tìm thấy màn hình / đường dẫn không hợp lệ").
 *
 * This is the shipment analogue of the already-solved contract boundary
 * (`lib/contractRoute.ts`): encode the IDENTITY, never the composed URL, so a
 * query string or `#anchor` is appended AFTER the encoded segment by the caller.
 *
 * The router's own resolution already exposes the original identity to
 * `useParams().id` (a single decode per segment; `%2F` is re-escaped before
 * matching and normalised back to `/` for the param value), so ShipmentDetail
 * keeps using the param directly and must NOT decode it a second time.
 */
export function shipmentPath(id: string): string {
  return "/lo-hang/" + encodeURIComponent(id);
}

/**
 * The exact shipment identity of the CURRENT location.
 *
 * A correctly encoded segment still cannot carry ONE identity class through
 * `useParams()`: React Router 7 normalises a decoded param by replacing `%2F`
 * with `/`, so an identity that literally contains an uppercase `%2F`
 * (e.g. `A%2FB`, sent as `A%252FB`) arrives as `A/B`. The raw location segment
 * — which is exactly the encoded segment the link carried — is therefore
 * decoded ONCE here, which is the same bounded mechanism the adjacent contract
 * detail has used since Issue #59 ("decode the original location segment
 * exactly ONCE"), and it is why exactly one decode must exist: an identity
 * carrying a literal `%20`/`%25` decodes to itself, never further.
 *
 * `paramId` remains the fallback for any location that is not this route.
 */
export function shipmentIdFromPath(pathname: string, paramId?: string): string {
  const fallback = paramId ?? "";
  const prefix = "/lo-hang/";
  if (!pathname.startsWith(prefix)) return fallback;
  const raw = pathname.slice(prefix.length).replace(/\/+$/, "");
  // A matched `/lo-hang/:id` location holds exactly one segment.
  if (raw === "" || raw.includes("/")) return fallback;
  try {
    return decodeURIComponent(raw);
  } catch {
    // Malformed percent-encoding: keep the router's own value, never a guess.
    return fallback;
  }
}
