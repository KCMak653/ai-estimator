// Minimal subset of window-quote-app's types/quote.ts — just what
// windowDiagram.ts and the estimate PDF need. Kept structurally identical so
// the diagram module can be re-synced from the quote app without edits.

export type StyleEnum =
  | ''
  | 'SSL'
  | 'SH'
  | 'DH'
  | 'DSL'
  | 'AW'
  | 'TT_HR'
  | 'TT_HL'
  | 'PD'
  | 'FIX'
  | 'PIC'
  | 'CS';

export type WindowColour = 'White' | 'Black';

export interface QuoteItemUnit {
  id: string;
  style: StyleEnum;
  width: number;
  height: number;
  exteriorColour?: WindowColour;
  hingeSide?: 'left' | 'right';
}

export interface QuoteItem {
  overallWidth: number;
  overallHeight: number;
  configuration?: { rows?: number; cols?: number };
  units: QuoteItemUnit[];
}

export const STYLE_DISPLAY_NAMES: Record<StyleEnum, string> = {
  '':    '',
  SSL:   'Single Slider',
  SH:    'Single Hung',
  DH:    'Double Hung',
  DSL:   'Double Slider',
  AW:    'Awning',
  TT_HR: 'Tilt & Turn (Hinge Right)',
  TT_HL: 'Tilt & Turn (Hinge Left)',
  PD:    'Patio Door',
  FIX:   'Fixed',
  PIC:   'Picture',
  CS:    'Casement',
};
