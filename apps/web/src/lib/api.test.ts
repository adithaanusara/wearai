import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  ApiError,
  buildQuery,
  getProduct,
  getMe,
  getMyOrders,
  getProductsByIds,
  getRelatedProducts,
  login,
  logout,
  orNotFound,
  placeOrder,
  quoteCart,
  register,
  searchProducts,
} from '@/lib/api';
import type { OrderRequest } from '@/types/api';

function respond(status: number, body: unknown) {
  // A new Response for every call, because a response body can only be read once.
  return vi.fn().mockImplementation(
    () =>
      new Response(typeof body === 'string' ? body : JSON.stringify(body), {
        status,
        headers: { 'Content-Type': 'application/json' },
      }),
  );
}

afterEach(() => vi.unstubAllGlobals());

describe('buildQuery', () => {
  it('returns an empty string when there is nothing to send', () => {
    expect(buildQuery()).toBe('');
    expect(buildQuery({ a: undefined, b: '' })).toBe('');
  });

  it('repeats the key for arrays and skips empty values', () => {
    expect(buildQuery({ size: ['M', 'L'], min: 3000, sort: undefined, q: '' })).toBe(
      '?size=M&size=L&min=3000',
    );
  });

  it('encodes special characters', () => {
    expect(buildQuery({ q: 'black & white/tee' })).toBe('?q=black+%26+white%2Ftee');
  });

  it('skips empty items inside arrays', () => {
    expect(buildQuery({ size: ['', 'M', ''] })).toBe('?size=M');
    expect(buildQuery({ size: [''] })).toBe('');
  });

  it('keeps zero, which is a real value', () => {
    expect(buildQuery({ min: 0 })).toBe('?min=0');
  });
});

describe('requests', () => {
  it('calls the versioned API without caching and returns the JSON', async () => {
    const fetchMock = respond(200, { id: 'w-tee-01' });
    vi.stubGlobal('fetch', fetchMock);

    await expect(getProduct('essential-fitted-tee')).resolves.toEqual({ id: 'w-tee-01' });

    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe('http://localhost:8000/api/v1/products/essential-fitted-tee');
    expect(options.cache).toBe('no-store');
  });

  it('encodes slugs so they cannot change the request path', async () => {
    const fetchMock = respond(404, { detail: 'Product not found' });
    vi.stubGlobal('fetch', fetchMock);

    await expect(getProduct('../health')).rejects.toBeInstanceOf(ApiError);

    expect(fetchMock.mock.calls[0][0]).toBe('http://localhost:8000/api/v1/products/..%2Fhealth');
  });

  it('sends related-products limits and search pages as query parameters', async () => {
    const related = respond(200, []);
    vi.stubGlobal('fetch', related);
    await getRelatedProducts('tee', 6);
    expect(related.mock.calls[0][0]).toContain('/products/tee/related?limit=6');

    const search = respond(200, { items: [] });
    vi.stubGlobal('fetch', search);
    await searchProducts('black hoodie', 2);
    expect(search.mock.calls[0][0]).toContain('/search?q=black+hoodie&page=2');
  });

  it('leaves page 1 out of the search query', async () => {
    const search = respond(200, { items: [] });
    vi.stubGlobal('fetch', search);

    await searchProducts('tee');

    expect(search.mock.calls[0][0]).toMatch(/\/search\?q=tee$/);
  });
});

describe('cart and checkout requests', () => {
  it('looks products up by id in one request', async () => {
    const fetchMock = respond(200, { items: [] });
    vi.stubGlobal('fetch', fetchMock);

    await getProductsByIds(['w-tee-01', 'm-jog-01']);

    expect(fetchMock.mock.calls[0][0]).toBe(
      'http://localhost:8000/api/v1/products?id=w-tee-01&id=m-jog-01&pageSize=100',
    );
  });

  it('asks the server to price a cart with a JSON POST', async () => {
    const fetchMock = respond(200, { lines: [], subtotal: 0, shipping: 0, total: 0 });
    vi.stubGlobal('fetch', fetchMock);
    const items = [{ productId: 'w-tee-01', size: 'M', quantity: 2 }];

    await quoteCart(items, 'express');

    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe('http://localhost:8000/api/v1/checkout/quote');
    expect(options.method).toBe('POST');
    expect(options.headers['Content-Type']).toBe('application/json');
    expect(JSON.parse(options.body)).toEqual({ items, deliveryMethod: 'express' });
  });

  it('sends the idempotency key with an order and never any prices', async () => {
    const fetchMock = respond(201, { reference: 'WA-TEST' });
    vi.stubGlobal('fetch', fetchMock);
    const order: OrderRequest = {
      items: [{ productId: 'w-tee-01', size: 'M', quantity: 1 }],
      deliveryMethod: 'standard',
      paymentMethod: 'cod',
      email: 'a@example.com',
      phone: '0771234567',
      fullName: 'A',
      address1: 'B',
      address2: '',
      city: 'C',
      province: 'Western',
      district: 'Colombo',
      postalCode: '10250',
    };

    await placeOrder({ ...order, expectedTotal: 6950 }, 'key-12345678');

    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe('http://localhost:8000/api/v1/orders');
    expect(options.headers['Idempotency-Key']).toBe('key-12345678');
    const sent = JSON.parse(options.body);
    // The total the shopper saw is sent for comparison; no price, shipping or subtotal ever is.
    expect(sent.expectedTotal).toBe(6950);
    expect(Object.keys(sent).join()).not.toMatch(/price|shipping|subtotal/i);
  });

  it('does not send a body or content type on plain reads', async () => {
    const fetchMock = respond(200, {});
    vi.stubGlobal('fetch', fetchMock);

    await getProduct('tee');

    const options = fetchMock.mock.calls[0][1];
    expect(options.method).toBe('GET');
    expect(options.body).toBeUndefined();
    expect(options.headers['Content-Type']).toBeUndefined();
  });
});

describe('authentication requests', () => {
  it('signs in with a JSON POST of the credentials only', async () => {
    const fetchMock = respond(200, { id: 1, name: 'A', email: 'a@example.com' });
    vi.stubGlobal('fetch', fetchMock);

    await expect(login('a@example.com', 'sunrise2026')).resolves.toMatchObject({ id: 1 });

    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe('http://localhost:8000/api/v1/auth/login');
    expect(options.method).toBe('POST');
    expect(JSON.parse(options.body)).toEqual({ email: 'a@example.com', password: 'sunrise2026' });
  });

  it('registers with name, email and password', async () => {
    const fetchMock = respond(201, { id: 2, name: 'N', email: 'n@example.com' });
    vi.stubGlobal('fetch', fetchMock);

    await register('N', 'n@example.com', 'sunrise2026');

    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      name: 'N',
      email: 'n@example.com',
      password: 'sunrise2026',
    });
  });

  it('logs out without trying to read a body', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 204 })));

    await expect(logout()).resolves.toBeUndefined();
  });

  it('asks the session endpoint and returns the user', async () => {
    const fetchMock = respond(200, { user: { id: 1, name: 'A', email: 'a@example.com' } });
    vi.stubGlobal('fetch', fetchMock);

    await expect(getMe()).resolves.toEqual({ id: 1, name: 'A', email: 'a@example.com' });

    expect(fetchMock.mock.calls[0][0]).toBe('http://localhost:8000/api/v1/auth/session');
  });

  it('returns null for a visitor, without any error', async () => {
    vi.stubGlobal('fetch', respond(200, { user: null }));

    await expect(getMe()).resolves.toBeNull();
  });

  it('still reports real failures', async () => {
    vi.stubGlobal('fetch', respond(500, { detail: 'boom' }));

    await expect(getMe()).rejects.toMatchObject({ status: 500 });
  });

  it('passes the cookie on when a server component asks', async () => {
    const fetchMock = respond(200, { id: 1, name: 'A', email: 'a@example.com' });
    vi.stubGlobal('fetch', fetchMock);

    await getMe({ Cookie: 'session=abc' });

    expect(fetchMock.mock.calls[0][1].headers.Cookie).toBe('session=abc');
  });

  it('asks for a page of orders with the cookie', async () => {
    const fetchMock = respond(200, { items: [], total: 0, page: 2, pageSize: 24 });
    vi.stubGlobal('fetch', fetchMock);

    await getMyOrders(2, { Cookie: 'session=abc' });
    await getMyOrders(1);

    expect(fetchMock.mock.calls[0][0]).toBe('http://localhost:8000/api/v1/orders?page=2');
    expect(fetchMock.mock.calls[0][1].headers.Cookie).toBe('session=abc');
    expect(fetchMock.mock.calls[1][0]).toBe('http://localhost:8000/api/v1/orders');
  });
});

describe('structured errors', () => {
  it('reads a code, message and extra facts from an object detail', async () => {
    vi.stubGlobal(
      'fetch',
      respond(409, {
        detail: { code: 'price_changed', message: 'Prices changed.', total: 8450 },
      }),
    );

    const error = await quoteCart([], 'standard').catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 409,
      message: 'Prices changed.',
      code: 'price_changed',
      details: { total: 8450 },
    });
  });

  it('has no code for a plain string error', async () => {
    vi.stubGlobal('fetch', respond(404, { detail: 'Product not found' }));

    const error = (await getProduct('x').catch((e: unknown) => e)) as ApiError;

    expect(error.code).toBeNull();
    expect(error.details).toEqual({});
  });

  it('falls back to a generic message for an object detail without one', async () => {
    vi.stubGlobal('fetch', respond(409, { detail: { code: 'odd' } }));

    await expect(quoteCart([], 'standard')).rejects.toMatchObject({
      message: 'Request failed (409)',
      code: 'odd',
    });
  });
});

describe('errors', () => {
  it('exposes field problems from a 422 so forms can show them', async () => {
    vi.stubGlobal(
      'fetch',
      respond(422, {
        detail: [
          { loc: ['body', 'email'], msg: 'Enter a valid email address.', type: 'value_error' },
          { loc: ['body', 'items', 1, 'size'], msg: 'Size unavailable.', type: 'value_error' },
        ],
      }),
    );

    const error = await quoteCart([], 'standard').catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 422, message: 'Enter a valid email address.' });
    expect((error as ApiError).problems.map((p) => p.loc)).toEqual([
      ['body', 'email'],
      ['body', 'items', 1, 'size'],
    ]);
  });

  it('ignores malformed problem entries', async () => {
    vi.stubGlobal('fetch', respond(422, { detail: [{ nope: 1 }, 'text', null] }));

    const error = await quoteCart([], 'standard').catch((e: unknown) => e);

    expect(error).toMatchObject({ status: 422, problems: [], message: 'Request failed (422)' });
  });

  it('turns an API error into an ApiError with the status and message', async () => {
    vi.stubGlobal('fetch', respond(404, { detail: 'Product not found' }));

    const error = await getProduct('nope').catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 404, message: 'Product not found' });
  });

  it('falls back to a generic message when the body is not the expected JSON', async () => {
    vi.stubGlobal('fetch', respond(500, '<html>oops</html>'));

    await expect(getProduct('x')).rejects.toMatchObject({
      status: 500,
      message: 'Request failed (500)',
    });
  });

  it('reports an unreachable API as 503', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('fetch failed')));

    await expect(getProduct('x')).rejects.toMatchObject({ status: 503 });
  });
});

describe('orNotFound', () => {
  it('passes results through', async () => {
    await expect(orNotFound(Promise.resolve(42))).resolves.toBe(42);
  });

  it('shows the not-found page for a 404', async () => {
    const rejection = orNotFound(Promise.reject(new ApiError(404, 'gone')));

    await expect(rejection).rejects.toMatchObject({ digest: expect.stringMatching(/404/) });
  });

  it('rethrows every other error unchanged', async () => {
    const failure = new ApiError(500, 'boom');

    await expect(orNotFound(Promise.reject(failure))).rejects.toBe(failure);
  });
});
