import { notFound } from 'next/navigation';
import type { CollectionPage, Page, ProductDetail, Review } from '@/types/api';
import type { Product } from '@/types/product';

/**
 * Client for the store API, for use in server components. The browser reaches the API through
 * the /api proxy instead (see next.config.ts), so this module reads a server-side setting.
 */
const API_URL = process.env.API_URL ?? 'http://localhost:8000';

export const MAX_QUERY_LENGTH = 100;

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

type QueryValue = string | number | undefined | (string | number)[];

/** Builds `?a=1&b=x&b=y`. Undefined and empty values are left out; arrays repeat the key. */
export function buildQuery(query: Record<string, QueryValue> = {}): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === '') continue;
    for (const item of Array.isArray(value) ? value : [value]) {
      if (item !== '') params.append(key, String(item));
    }
  }
  const text = params.toString();
  return text ? `?${text}` : '';
}

async function readDetail(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    const detail = (body as { detail?: unknown }).detail;
    if (typeof detail === 'string') return detail;
  } catch {
    // Not JSON; fall through to the generic message.
  }
  return `Request failed (${response.status})`;
}

async function request<T>(path: string, query?: Record<string, QueryValue>): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/v1${path}${buildQuery(query)}`, {
      cache: 'no-store',
      headers: { Accept: 'application/json' },
    });
  } catch {
    throw new ApiError(503, 'The store service is unavailable.');
  }
  if (!response.ok) throw new ApiError(response.status, await readDetail(response));
  return (await response.json()) as T;
}

/** Shows the site's 404 page when the API says the thing does not exist. */
export async function orNotFound<T>(promise: Promise<T>): Promise<T> {
  try {
    return await promise;
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  }
}

// Slugs come from the URL, so they are encoded to keep them from changing the request path.
const segment = encodeURIComponent;

export const getProducts = (query?: Record<string, QueryValue>) =>
  request<Page<Product>>('/products', query);

export const getCollection = (slug: string, query?: Record<string, QueryValue>) =>
  request<CollectionPage>(`/collections/${segment(slug)}`, query);

export const getProduct = (slug: string) => request<ProductDetail>(`/products/${segment(slug)}`);

export const getReviews = (slug: string) => request<Review[]>(`/products/${segment(slug)}/reviews`);

export const getRelatedProducts = (slug: string, limit = 4) =>
  request<Product[]>(`/products/${segment(slug)}/related`, { limit });

export const searchProducts = (query: string, page = 1) =>
  request<Page<Product>>('/search', { q: query, page: page > 1 ? page : undefined });
