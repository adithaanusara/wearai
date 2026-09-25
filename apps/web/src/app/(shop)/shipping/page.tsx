import type { Metadata } from 'next';
import { PolicyHeading, PolicyPage } from '@/components/layout/PolicyPage';
import { deliveryMethods } from '@/data/shipping';
import { formatPrice } from '@/lib/format';

export const metadata: Metadata = { title: 'Shipping policy' };

export default function ShippingPage() {
  return (
    <PolicyPage title="Shipping policy">
      <p>We deliver across Sri Lanka. Choose a delivery method at checkout.</p>

      <table className="w-full text-left">
        <caption className="sr-only">Delivery methods, fees and delivery times</caption>
        <thead>
          <tr className="border-border border-b">
            <th scope="col" className="py-2 pr-4 font-medium">
              Method
            </th>
            <th scope="col" className="py-2 pr-4 font-medium">
              Delivery time
            </th>
            <th scope="col" className="py-2 font-medium">
              Fee
            </th>
          </tr>
        </thead>
        <tbody>
          {deliveryMethods.map((method) => (
            <tr key={method.id} className="border-border border-b align-top">
              <th scope="row" className="py-3 pr-4 font-medium">
                {method.label}
              </th>
              <td className="py-3 pr-4">{method.estimate}</td>
              <td className="py-3">
                {method.fee === 0 ? 'Free' : formatPrice(method.fee)}
                {method.freeOver !== undefined && (
                  <span className="text-muted block text-xs">
                    Free over {formatPrice(method.freeOver)}
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <PolicyHeading>Good to know</PolicyHeading>
      <ul className="list-disc space-y-2 pl-5">
        <li>Delivery times are estimates.</li>
        <li>You will need a Sri Lankan mobile number so the courier can reach you.</li>
        <li>Prices include tax. The delivery fee is shown before you place your order.</li>
      </ul>
    </PolicyPage>
  );
}
