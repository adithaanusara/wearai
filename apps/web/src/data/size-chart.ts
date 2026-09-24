export interface SizeChartRow {
  size: string;
  chest: number;
  waist: number;
  hip: number;
}

/** Body measurements in centimetres. */
export const sizeChart: SizeChartRow[] = [
  { size: 'XS', chest: 80, waist: 62, hip: 88 },
  { size: 'S', chest: 86, waist: 68, hip: 94 },
  { size: 'M', chest: 92, waist: 74, hip: 100 },
  { size: 'L', chest: 98, waist: 80, hip: 106 },
  { size: 'XL', chest: 104, waist: 86, hip: 112 },
];
