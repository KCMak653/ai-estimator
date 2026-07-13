// Customer-facing ESTIMATE PDF for the chat estimator.
// Lean sibling of window-quote-app's pdfGenerator.ts: same design language
// (letter page, header band, item rows with window diagrams, totals block),
// but prices are RANGES and the document is explicitly an estimate, not a
// contract. Input is the chatbot's display_dict + raw window config.

import { jsPDF } from 'jspdf';
import { drawWindowDiagramPdf } from './windowDiagram';
import { STYLE_DISPLAY_NAMES } from './types';
import { LOGO_PNG_B64, LOGO_ASPECT } from './logo';

// ── Design tokens (Direct Windows green) ─────────────────────────────────────
const ACCENT       = [46, 64, 52];    // #2E4034
const TEXT_PRIMARY = [31, 44, 36];    // #1F2C24
const TEXT_MUTED   = [96, 108, 100];
const DIVIDER      = [225, 228, 224];
const BG_SUBTLE    = [246, 247, 245];

const PAGE_W = 8.5;
const PAGE_H = 11;
const MX = 0.55;
const CONTENT_W = PAGE_W - MX * 2;
const FOOTER_H = 0.55;

const COMPANY_NAME    = 'Direct Windows & Doors';
const COMPANY_PHONE   = '(365) 832-8589';
const COMPANY_EMAIL   = 'info@directwindows.ca';
const COMPANY_ADDRESS = '1060 Sheppard Ave W, Toronto, ON M3J 0G7';
const COMPANY_SITE    = 'directwindows.ca';

const UNIT_TYPE_TO_STYLE = {
  casement: 'CS',
  awning: 'AW',
  picture_window: 'PIC',
  fixed_casement: 'FIX',
  single_slider: 'SSL',
  single_hung: 'SH',
  double_hung: 'DH',
  double_slider: 'DSL',
};

const dollars = (n) => '$' + Math.round(n || 0).toLocaleString('en-CA');
const range = (lo, hi) => `${dollars(lo)} – ${dollars(hi)}`;

function windowKeys(obj) {
  return Object.keys(obj || {})
    .filter((k) => k.startsWith('window_'))
    .sort((a, b) => Number(a.slice(7)) - Number(b.slice(7)));
}

/** Build a diagram QuoteItem from the chatbot's raw window config + breakdown row. */
function toDiagramItem(winConfig, row) {
  const overallWidth = Number(row.width) || Number(winConfig?.width) || 0;
  const overallHeight = Number(row.height) || Number(winConfig?.height) || 0;
  const exteriorColour = String(row.exterior || '').toLowerCase() === 'black' ? 'Black' : 'White';

  const unitsSrc = (winConfig && winConfig.units) || {};
  const unitKeys = Object.keys(unitsSrc)
    .filter((k) => k.startsWith('unit_'))
    .sort((a, b) => Number(a.slice(5)) - Number(b.slice(5)));

  let units = unitKeys.map((k) => {
    const u = unitsSrc[k] || {};
    const frac = Number(u.window_area_frac) > 0 ? Number(u.window_area_frac) : 1 / unitKeys.length;
    return {
      id: '',
      style: UNIT_TYPE_TO_STYLE[String(u.unit_type || '').toLowerCase()] || 'FIX',
      width: overallWidth * frac,
      height: overallHeight,
      exteriorColour,
    };
  });
  if (units.length === 0) {
    units = [{ id: '', style: 'FIX', width: overallWidth || 30, height: overallHeight || 30, exteriorColour }];
  }
  return {
    overallWidth,
    overallHeight,
    configuration: { rows: 1, cols: units.length },
    units,
  };
}

function setText(doc, size, color, style = 'normal') {
  doc.setFont('helvetica', style);
  doc.setFontSize(size);
  doc.setTextColor(color[0], color[1], color[2]);
}

function hr(doc, y, color = DIVIDER) {
  doc.setDrawColor(color[0], color[1], color[2]);
  doc.setLineWidth(0.01);
  doc.line(MX, y, PAGE_W - MX, y);
}

function footer(doc) {
  const y = PAGE_H - FOOTER_H + 0.08;
  hr(doc, y);
  setText(doc, 8, TEXT_MUTED);
  doc.text(
    `${COMPANY_NAME}  ·  ${COMPANY_PHONE}  ·  ${COMPANY_EMAIL}  ·  ${COMPANY_SITE}`,
    PAGE_W / 2, y + 0.14, { align: 'center', baseline: 'top' },
  );
}

export function generateEstimatePdf(payload) {
  const dd = payload.display_dict || {};
  const config = payload.config || {};
  const breakdown = dd.breakdown || {};
  const keys = windowKeys(breakdown);
  const installationReq = !!dd.installation_req;

  const doc = new jsPDF({ unit: 'in', format: 'letter', compress: true });

  // ── Header ────────────────────────────────────────────────────────────────
  const logoH = 0.72;
  const logoW = logoH * LOGO_ASPECT;
  try { doc.addImage(LOGO_PNG_B64, 'PNG', MX, 0.5, logoW, logoH); } catch { /* logo optional */ }

  const infoX = MX + logoW + 0.18;
  setText(doc, 13, TEXT_PRIMARY, 'bold');
  doc.text(COMPANY_NAME, infoX, 0.54, { baseline: 'top' });
  setText(doc, 8.5, TEXT_MUTED);
  doc.text(`${COMPANY_PHONE}  ·  ${COMPANY_EMAIL}`, infoX, 0.76, { baseline: 'top' });
  doc.text(COMPANY_ADDRESS, infoX, 0.89, { baseline: 'top' });
  doc.text(COMPANY_SITE, infoX, 1.02, { baseline: 'top' });

  setText(doc, 21, ACCENT, 'bold');
  doc.text('ESTIMATE', PAGE_W - MX, 0.54, { align: 'right', baseline: 'top' });
  setText(doc, 9, TEXT_MUTED);
  if (payload.quote_id) doc.text(`Ref: ${payload.quote_id}`, PAGE_W - MX, 0.87, { align: 'right', baseline: 'top' });
  if (payload.date) doc.text(payload.date, PAGE_W - MX, 1.00, { align: 'right', baseline: 'top' });
  if (payload.email) doc.text(`Prepared for: ${payload.email}`, PAGE_W - MX, 1.13, { align: 'right', baseline: 'top' });

  let y = 1.42;
  hr(doc, y);
  y += 0.22;

  // ── Window rows ───────────────────────────────────────────────────────────
  const DIAG_W = 1.35;
  const DIAG_H = 1.05;
  const ROW_GAP = 0.18;

  for (const key of keys) {
    const row = breakdown[key] || {};
    const winEntry = config[key] || {};
    const rowH = Math.max(DIAG_H, 0.95) + ROW_GAP;

    if (y + rowH > PAGE_H - FOOTER_H - 1.0) {
      footer(doc);
      doc.addPage();
      y = 0.6;
    }

    // Diagram
    try {
      const item = toDiagramItem(winEntry.config, row);
      if (item.overallWidth > 0 && item.overallHeight > 0) {
        // drawWindowDiagramPdf draws in diagram-model units scaled to the box we give it
        drawScaledDiagram(doc, item, MX, y, DIAG_W, DIAG_H);
      }
    } catch { /* diagram is decoration; never block the estimate */ }

    const textX = MX + DIAG_W + 0.25;
    const qty = row.quantity || 1;
    const label = key.replace('_', ' ').replace(/^w/, 'W');
    const typeName = row.type && row.type !== '—' ? row.type : 'Window';

    setText(doc, 11.5, TEXT_PRIMARY, 'bold');
    doc.text(`${label} — ${typeName}`, textX, y + 0.02, { baseline: 'top' });

    setText(doc, 9.5, TEXT_MUTED);
    const dims = row.width != null && row.height != null ? `${row.width}"W × ${row.height}"H` : '';
    doc.text(dims, textX, y + 0.24, { baseline: 'top' });
    doc.text(`Interior: ${row.interior || '—'}   ·   Exterior: ${row.exterior || '—'}`, textX, y + 0.40, { baseline: 'top' });
    doc.text(`Quantity: ${qty}`, textX, y + 0.56, { baseline: 'top' });

    // Price range, right-aligned
    const unitLo = row.unit_price_min_adjusted || 0;
    const unitHi = row.unit_price_max_adjusted || 0;
    setText(doc, 11.5, TEXT_PRIMARY, 'bold');
    doc.text(range(unitLo * (qty > 1 ? 1 : qty), unitHi), PAGE_W - MX, y + 0.02, { align: 'right', baseline: 'top' });
    setText(doc, 8.5, TEXT_MUTED);
    if (qty > 1) {
      doc.text('per window', PAGE_W - MX, y + 0.24, { align: 'right', baseline: 'top' });
      doc.text(`Line total: ${range(row.price_min_adjusted || unitLo * qty, row.price_max_adjusted || unitHi * qty)}`,
        PAGE_W - MX, y + 0.40, { align: 'right', baseline: 'top' });
    }

    y += rowH;
    hr(doc, y - ROW_GAP / 2);
    y += 0.06;
  }

  // ── Totals ────────────────────────────────────────────────────────────────
  if (y + 1.6 > PAGE_H - FOOTER_H - 1.0) {
    footer(doc);
    doc.addPage();
    y = 0.6;
  }
  y += 0.12;
  const labelX = PAGE_W - MX - 2.9;
  const valueX = PAGE_W - MX;

  const showWindowsTotal = (dd.multi_unit || dd.any_quant_gt_1) === true;
  if (showWindowsTotal) {
    setText(doc, 9.5, TEXT_MUTED);
    doc.text('Windows subtotal', labelX, y, { baseline: 'top' });
    doc.text(range(dd.windows_total_min_adjusted, dd.windows_total_max_adjusted), valueX, y, { align: 'right', baseline: 'top' });
    y += 0.22;
  }
  if (installationReq && (dd.installation_min_adjusted || 0) > 0) {
    const [lo, hi] = [dd.installation_min_adjusted, dd.installation_max_adjusted].sort((a, b) => a - b);
    setText(doc, 9.5, TEXT_MUTED);
    doc.text('Installation', labelX, y, { baseline: 'top' });
    doc.text(range(lo, hi), valueX, y, { align: 'right', baseline: 'top' });
    y += 0.22;
  }
  doc.setDrawColor(ACCENT[0], ACCENT[1], ACCENT[2]);
  doc.setLineWidth(0.014);
  doc.line(labelX, y + 0.02, valueX, y + 0.02);
  y += 0.12;
  setText(doc, 13, ACCENT, 'bold');
  doc.text('Estimated total', labelX, y, { baseline: 'top' });
  doc.text(range(dd.total_min_adjusted, dd.total_max_adjusted), valueX, y, { align: 'right', baseline: 'top' });
  setText(doc, 8.5, TEXT_MUTED);
  if (installationReq) doc.text('including installation', labelX, y + 0.24, { baseline: 'top' });
  doc.text('+ HST', valueX, y + 0.24, { align: 'right', baseline: 'top' });
  y += 0.5;

  // ── About this estimate ───────────────────────────────────────────────────
  const NOTE_LINES = [
    'This is an approximate estimate based on the sizes and details you described — it is not a contract or a firm quote.',
    `Your final price is confirmed after a free, no-obligation exact measure at your home. Book yours at ${COMPANY_PHONE}.`,
    'Prices are in Canadian dollars and exclude HST. If the measure turns up something this estimate couldn’t know about, we tell you before you commit to anything.',
  ];
  setText(doc, 8.7, TEXT_MUTED);
  const wrapped = NOTE_LINES.map((l) => doc.splitTextToSize('•  ' + l, CONTENT_W - 0.5));
  const noteH = 0.34 + wrapped.reduce((s, w) => s + w.length * 0.15 + 0.06, 0);
  if (y + noteH > PAGE_H - FOOTER_H - 0.1) {
    footer(doc);
    doc.addPage();
    y = 0.6;
  }
  doc.setFillColor(BG_SUBTLE[0], BG_SUBTLE[1], BG_SUBTLE[2]);
  doc.roundedRect(MX, y, CONTENT_W, noteH, 0.08, 0.08, 'F');
  let ny = y + 0.16;
  setText(doc, 9.5, TEXT_PRIMARY, 'bold');
  doc.text('About this estimate', MX + 0.22, ny, { baseline: 'top' });
  ny += 0.24;
  setText(doc, 8.7, TEXT_MUTED);
  for (const lines of wrapped) {
    doc.text(lines, MX + 0.22, ny, { baseline: 'top' });
    ny += lines.length * 0.15 + 0.06;
  }

  footer(doc);
  return doc;
}

/**
 * The diagram builder emits shapes in a ~120x90 abstract space; scale them into
 * an inch-sized box. jsPDF has no transform stack we can rely on across
 * versions, so scale via a wrapper doc proxy is overkill — instead we scale
 * the item box by drawing into a temporary scaled coordinate frame:
 * buildCombinationDiagram already fits to (maxWidth, maxHeight) in the units
 * we pass, so passing inches directly just works.
 */
function drawScaledDiagram(doc, item, x, y, maxW, maxH) {
  drawWindowDiagramPdf(doc, item, x, y, maxW, maxH);
}
