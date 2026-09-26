'use client';

import { useQuery } from '@tanstack/react-query';
import { ChatProductCard } from '@/components/chat/ChatProductCard';
import { getProductsByIds } from '@/lib/api';

interface ChatProductsProps {
  ids: string[];
  onNavigate: () => void;
}

/** The product cards under an assistant message. The assistant only names products by id. */
export function ChatProducts({ ids, onNavigate }: ChatProductsProps) {
  const { data } = useQuery({
    queryKey: ['chat-products', ids],
    queryFn: () => getProductsByIds(ids),
    staleTime: 60_000,
  });

  const byId = new Map(data?.items.map((product) => [product.id, product]));
  // Kept in the order the assistant chose. A product that no longer exists is simply left out.
  const products = ids.flatMap((id) => byId.get(id) ?? []);
  if (products.length === 0) return null;

  return (
    <ul className="w-full max-w-[85%] space-y-2">
      {products.map((product) => (
        <li key={product.id}>
          <ChatProductCard product={product} onNavigate={onNavigate} />
        </li>
      ))}
    </ul>
  );
}
