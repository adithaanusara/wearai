// Unsplash resizes on its side through the query string, so a tile never downloads a full-size
// original. next/image then serves the final size for each screen from that.
export function unsplash(id: string, width = 800): string {
  return `https://images.unsplash.com/photo-${id}?auto=format&fit=crop&w=${width}&q=80`;
}
