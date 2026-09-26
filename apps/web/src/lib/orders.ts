/** "pending" becomes "Pending". The statuses come from the API. */
export function statusLabel(status: string): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}
