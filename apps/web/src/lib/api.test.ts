import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  ApiError,
  buildQuery,
  getProduct,
  getRelatedProducts,
  orNotFound,
  searchProducts,
} from '@/lib/api';

function respond(status: number, body: unknown) {
  return vi.fn().mockResolvedValue(
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

describe('errors', () => {
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
