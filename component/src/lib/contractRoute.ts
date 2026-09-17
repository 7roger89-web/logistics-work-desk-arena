/** A contract number is one route segment, even when it contains slashes. */
export function contractPath(id: string): string {
  return "/hop-dong/" + encodeURIComponent(id);
}
