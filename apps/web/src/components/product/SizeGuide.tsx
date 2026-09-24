'use client';

import { useState } from 'react';
import { Drawer } from '@/components/ui/Drawer';
import { sizeChart } from '@/data/size-chart';

export function SizeGuide() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        className="text-xs underline"
        aria-haspopup="dialog"
        onClick={() => setOpen(true)}
      >
        Size guide
      </button>

      <Drawer open={open} onClose={() => setOpen(false)} title="Size guide">
        <div className="flex-1 overflow-y-auto p-(--gutter)">
          <table className="w-full text-left text-sm">
            <caption className="text-muted mb-3 text-left text-xs">
              Body measurements in centimetres.
            </caption>
            <thead>
              <tr className="border-border border-b">
                <th scope="col" className="py-2 font-medium">
                  Size
                </th>
                <th scope="col" className="py-2 font-medium">
                  Chest
                </th>
                <th scope="col" className="py-2 font-medium">
                  Waist
                </th>
                <th scope="col" className="py-2 font-medium">
                  Hip
                </th>
              </tr>
            </thead>
            <tbody>
              {sizeChart.map((row) => (
                <tr key={row.size} className="border-border border-b">
                  <th scope="row" className="py-3 font-medium">
                    {row.size}
                  </th>
                  <td className="py-3">{row.chest}</td>
                  <td className="py-3">{row.waist}</td>
                  <td className="py-3">{row.hip}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-muted mt-4 text-xs">
            Between sizes? Choose the larger size for a relaxed fit.
          </p>
        </div>
      </Drawer>
    </>
  );
}
