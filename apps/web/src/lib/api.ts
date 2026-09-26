import { notFound } from 'next/navigation';
import type {
  AdminUser,
  AuditEntry,
  CheckoutOptions,
  Dashboard,
  CollectionPage,
  Order,
  OrderRequest,
  Page,
  ProductDetail,
  Quote,
  Review,
  Role,
  User,
} from '@/types/api';
import type { CartItem } from '@/types/cart';
import type { ChatRequest, ChatResponse } from '@/types/chat';
import type { Product } from '@/types/product';

/**
 * Client for the store API. On the server it calls the API directly (API_URL); in the browser it
 * uses the same-origin /api proxy (see next.config.ts), so cookies work and there is no CORS.
 */
const API_URL = process.env.API_URL ?? 'http://localhost:8000';

const baseUrl = () => (typeof window === 'undefined' ? API_URL : '');

export const MAX_QUERY_LENGTH = 100;

/** One thing wrong with a request, as reported by the API (a 422). */
export interface ApiProblem {
  /** Where the problem is, such as ['body', 'email'] or ['body', 'items', 1, 'size']. */
  loc: (string | number)[];
  msg: string;
}

export class ApiError extends Error {
  readonly status: number;
  readonly problems: ApiProblem[];
  /** A machine-readable reason, such as "price_changed", when the API gives one. */
  readonly code: string | null;
  /** Extra facts that came with the error, such as the new total after a price change. */
  readonly details: Record<string, unknown>;

  constructor(
    status: number,
    message: string,
    problems: ApiProblem[] = [],
    extra: { code?: string; details?: Record<string, unknown> } = {},
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.problems = problems;
    this.code = extra.code ?? null;
    this.details = extra.details ?? {};
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

function isProblem(value: unknown): value is ApiProblem {
  const candidate = value as Partial<ApiProblem> | null;
  return Array.isArray(candidate?.loc) && typeof candidate?.msg === 'string';
}

async function readError(response: Response): Promise<ApiError> {
  const fallback = `Request failed (${response.status})`;
  try {
    const body: unknown = await response.json();
    const detail = (body as { detail?: unknown }).detail;
    if (typeof detail === 'string') return new ApiError(response.status, detail);
    if (detail && typeof detail === 'object' && !Array.isArray(detail)) {
      // A structured error: { code, message, ...facts }.
      const { code, message, ...details } = detail as Record<string, unknown>;
      return new ApiError(response.status, typeof message === 'string' ? message : fallback, [], {
        code: typeof code === 'string' ? code : undefined,
        details,
      });
    }
    if (Array.isArray(detail)) {
      const problems = detail.filter(isProblem);
      return new ApiError(response.status, problems[0]?.msg ?? fallback, problems);
    }
  } catch {
    // Not JSON; use the generic message.
  }
  return new ApiError(response.status, fallback);
}

interface RequestOptions {
  query?: Record<string, QueryValue>;
  method?: 'GET' | 'POST' | 'PATCH';
  body?: unknown;
  headers?: Record<string, string>;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { query, method = 'GET', body, headers } = options;

  let response: Response;
  try {
    response = await fetch(`${baseUrl()}/api/v1${path}${buildQuery(query)}`, {
      method,
      cache: 'no-store',
      headers: {
        Accept: 'application/json',
        ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
        ...headers,
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(503, 'The store service is unavailable.');
  }
  if (!response.ok) throw await readError(response);
  // A 204 (such as after logging out) has no body to read.
  if (response.status === 204) return undefined as T;
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
  request<Page<Product>>('/products', { query });

/** Looks up specific products, such as the ones in the cart. Ids that do not exist are missing. */
export const getProductsByIds = (ids: string[]) => getProducts({ id: ids, pageSize: 100 });

export const getCollection = (slug: string, query?: Record<string, QueryValue>) =>
  request<CollectionPage>(`/collections/${segment(slug)}`, { query });

export const getProduct = (slug: string) => request<ProductDetail>(`/products/${segment(slug)}`);

export const getReviews = (slug: string) => request<Review[]>(`/products/${segment(slug)}/reviews`);

export const getRelatedProducts = (slug: string, limit = 4) =>
  request<Product[]>(`/products/${segment(slug)}/related`, { query: { limit } });

export const searchProducts = (query: string, page = 1) =>
  request<Page<Product>>('/search', { query: { q: query, page: page > 1 ? page : undefined } });

export const getCheckoutOptions = () => request<CheckoutOptions>('/checkout/options');

/** The server's price for a cart. The browser's own arithmetic is for display only. */
export const quoteCart = (items: CartItem[], deliveryMethod: string) =>
  request<Quote>('/checkout/quote', { method: 'POST', body: { items, deliveryMethod } });

/** Places an order. Retrying with the same key returns the original order instead of a second one. */
export const placeOrder = (order: OrderRequest, idempotencyKey: string) =>
  request<Order>('/orders', {
    method: 'POST',
    body: order,
    headers: { 'Idempotency-Key': idempotencyKey },
  });

type AuthHeaders = Record<string, string>;

/**
 * The signed-in user, or null when nobody is. This asks /auth/session, which answers 200 either way,
 * so a visitor does not cause an error in the browser console on every page. The session cookie
 * travels with browser requests on its own; a server component has to pass it on through `headers`.
 */
export async function getMe(headers?: AuthHeaders): Promise<User | null> {
  const { user } = await request<{ user: User | null }>('/auth/session', { headers });
  return user;
}

export const login = (email: string, password: string) =>
  request<User>('/auth/login', { method: 'POST', body: { email, password } });

export const register = (name: string, email: string, password: string) =>
  request<User>('/auth/register', { method: 'POST', body: { name, email, password } });

export const logout = () => request<void>('/auth/logout', { method: 'POST' });

export const getMyOrders = (page = 1, headers?: AuthHeaders) =>
  request<Page<Order>>('/orders', { query: { page: page > 1 ? page : undefined }, headers });

/** Asks the shopping assistant. Only the conversation is sent: no prices, no personal data. */
export const sendChat = (messages: ChatRequest['messages']) =>
  request<ChatResponse>('/chat', { method: 'POST', body: { messages } });

// ---------- admin (each call is checked by the API; the website only chooses what to show) ----------

export const getAdminDashboard = (headers?: AuthHeaders) =>
  request<Dashboard>('/admin/dashboard', { headers });

export const getAdminUsers = (
  query: { search?: string; role?: string; page?: number },
  headers?: AuthHeaders,
) =>
  request<Page<AdminUser>>('/admin/users', {
    query: { ...query, page: query.page && query.page > 1 ? query.page : undefined },
    headers,
  });

export const changeUserRole = (userId: number, role: Role) =>
  request<AdminUser>(`/admin/users/${userId}/role`, { method: 'PATCH', body: { role } });

export const getAuditLog = (page = 1, headers?: AuthHeaders) =>
  request<Page<AuditEntry>>('/admin/audit-log', {
    query: { page: page > 1 ? page : undefined },
    headers,
  });
