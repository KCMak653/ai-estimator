import type { jsPDF } from 'jspdf'
import type { QuoteItem, QuoteItemUnit, StyleEnum, WindowColour } from './types'

type Point = { x: number; y: number }

type DiagramShape =
  | {
      kind: 'rect'
      x: number
      y: number
      width: number
      height: number
      stroke?: string
      fill?: string
      strokeWidth?: number
    }
  | {
      kind: 'line'
      from: Point
      to: Point
      stroke?: string
      strokeWidth?: number
    }
  | {
      kind: 'polyline'
      points: Point[]
      stroke?: string
      strokeWidth?: number
      fill?: string
    }
  | {
      kind: 'text'
      x: number
      y: number
      value: string
      color?: string
      fontSize?: number
      bold?: boolean
    }

interface DiagramModel {
  width: number
  height: number
  shapes: DiagramShape[]
}

const COLORS = {
  frameOuter: '#bdbdbd',
  frameInner: '#dddddd',
  glass: '#f7f7f7',
  divider: '#b8b8b8',
  hardware: '#9e9e9e',
  arrow: '#111111',
  mullion: '#8a8a8a',
  text: '#444444',
}

// Per-colour frame palettes. Only the two frame layers in pushFrameLayers
// change; glass, hardware, dividers, arrows, mullion all stay neutral.
const FRAME_PALETTE: Record<WindowColour, {
  outerFill: string; outerStroke: string; innerFill: string; innerStroke: string;
}> = {
  White: {
    outerFill: '#bdbdbd', outerStroke: '#9f9f9f',
    innerFill: '#dddddd', innerStroke: '#b4b4b4',
  },
  Black: {
    outerFill: '#1A1A1A', outerStroke: '#0F0F0F',
    innerFill: '#2A2A2A', innerStroke: '#333333',
  },
}

const DEFAULT_WIDTH = 120
const DEFAULT_HEIGHT = 90

// Named layout constants (combination diagrams)
// Mullion thickness is expressed in units of `u` (~ frame-thickness unit), so
// it scales with the diagram and reads as a structural member sized similarly
// to the outer frame on each unit.
const MULLION_THICKNESS_U = 4.5

// Picture-window frame thickness as a fraction of the regular frame. A picture
// window has no operating sash, so the visible frame profile is significantly
// narrower than an operable window of the same size.
const PICTURE_FRAME_SCALE = 0.55
function unitAspectRatio(unit: QuoteItemUnit): number {
  if (unit.width > 0 && unit.height > 0) return unit.width / unit.height
  return 1.25
}

function itemAspectRatio(item: QuoteItem): number {
  if (item.overallWidth > 0 && item.overallHeight > 0) {
    return item.overallWidth / item.overallHeight
  }
  // Fallback: derive from units honouring orientation. Vertical combos sum
  // heights and share width; horizontal combos sum widths and share height.
  const isVertical = (item.configuration?.rows ?? 1) > 1
  const totalW = isVertical
    ? item.units.reduce((max, u) => Math.max(max, u.width || 0), 0)
    : item.units.reduce((sum, u) => sum + (u.width || 0), 0)
  const totalH = isVertical
    ? item.units.reduce((sum, u) => sum + (u.height || 0), 0)
    : item.units.reduce((max, u) => Math.max(max, u.height || 0), 0)
  if (totalW > 0 && totalH > 0) return totalW / totalH
  return unitAspectRatio(item.units[0] ?? { width: 0, height: 0 } as QuoteItemUnit)
}

function fitBox(maxWidth: number, maxHeight: number, aspectRatio: number) {
  const boundedAspect = aspectRatio > 0 ? aspectRatio : 1.25
  let width = maxWidth
  let height = width / boundedAspect

  if (height > maxHeight) {
    height = maxHeight
    width = height * boundedAspect
  }

  return { width, height }
}

// ── Single-unit shape builder ─────────────────────────────────────────────────

interface UnitBox {
  x: number
  y: number
  width: number
  height: number
}

function pushFrameLayers(
  shapes: DiagramShape[],
  box: UnitBox,
  u: number,
  frameColour: WindowColour = 'White',
  thicknessScale = 1,
) {
  const palette = FRAME_PALETTE[frameColour]
  const t = u * thicknessScale
  shapes.push({
    kind: 'rect',
    x: box.x + t,
    y: box.y + t,
    width: box.width - t * 2,
    height: box.height - t * 2,
    fill: palette.outerFill,
    stroke: palette.outerStroke,
    strokeWidth: u * 2.2,
  })
  shapes.push({
    kind: 'rect',
    x: box.x + t * 4,
    y: box.y + t * 4,
    width: box.width - t * 8,
    height: box.height - t * 8,
    fill: palette.innerFill,
    stroke: palette.innerStroke,
    strokeWidth: u * 1.8,
  })
  shapes.push({
    kind: 'rect',
    x: box.x + t * 9,
    y: box.y + t * 9,
    width: box.width - t * 18,
    height: box.height - t * 18,
    fill: COLORS.glass,
    stroke: '#c2c2c2',
    strokeWidth: u * 1.2,
  })
}

function glassRect(box: UnitBox, u: number, thicknessScale = 1): UnitBox {
  const t = u * thicknessScale
  return {
    x: box.x + t * 9,
    y: box.y + t * 9,
    width: box.width - t * 18,
    height: box.height - t * 18,
  }
}

function addHandle(shapes: DiagramShape[], x: number, y: number, u: number, vertical = true) {
  const size = vertical ? { w: u * 0.8, h: u * 6 } : { w: u * 6, h: u * 0.8 }
  shapes.push({
    kind: 'rect',
    x: x - size.w / 2,
    y: y - size.h / 2,
    width: size.w,
    height: size.h,
    fill: COLORS.hardware,
    stroke: COLORS.hardware,
    strokeWidth: u * 0.5,
  })
}

function addArrow(shapes: DiagramShape[], from: Point, to: Point, u: number) {
  const dx = to.x - from.x
  const dy = to.y - from.y
  const length = Math.hypot(dx, dy) || 1
  const ux = dx / length
  const uy = dy / length
  const size = u * 4
  const base = { x: to.x - ux * size, y: to.y - uy * size }
  const perp = { x: -uy, y: ux }

  shapes.push({ kind: 'line', from, to, stroke: COLORS.arrow, strokeWidth: u * 2.2 })
  shapes.push({
    kind: 'polyline',
    points: [
      { x: base.x + perp.x * u * 2.2, y: base.y + perp.y * u * 2.2 },
      to,
      { x: base.x - perp.x * u * 2.2, y: base.y - perp.y * u * 2.2 },
    ],
    stroke: COLORS.arrow,
    strokeWidth: u * 2.2,
  })
}

// All decorations below operate on a **glass rect** so they compose cleanly
// for both single-unit and combination items (combinations share one outer
// frame and sub-divide its glass region).

function decorateFixed(_shapes: DiagramShape[], _glass: UnitBox, _u: number) {
  // No arrows, no hinge. The glass rect alone communicates a fixed window.
}

/** Standard casement symbol: triangle with apex at the hinge-side edge midpoint. */
function decorateCasement(
  shapes: DiagramShape[],
  glass: UnitBox,
  u: number,
  hingeSide: 'left' | 'right',
) {
  const apex = hingeSide === 'left'
    ? { x: glass.x, y: glass.y + glass.height / 2 }
    : { x: glass.x + glass.width, y: glass.y + glass.height / 2 }
  const baseTop = hingeSide === 'left'
    ? { x: glass.x + glass.width, y: glass.y }
    : { x: glass.x, y: glass.y }
  const baseBot = hingeSide === 'left'
    ? { x: glass.x + glass.width, y: glass.y + glass.height }
    : { x: glass.x, y: glass.y + glass.height }

  const stroke = COLORS.arrow
  const strokeWidth = u * 0.6
  shapes.push({ kind: 'line', from: apex, to: baseTop, stroke, strokeWidth })
  shapes.push({ kind: 'line', from: apex, to: baseBot, stroke, strokeWidth })
  shapes.push({ kind: 'line', from: baseTop, to: baseBot, stroke, strokeWidth })
}

function decorateDoubleHung(shapes: DiagramShape[], glass: UnitBox, u: number) {
  const splitY = glass.y + glass.height / 2
  shapes.push({
    kind: 'rect',
    x: glass.x,
    y: splitY - u * 1.2,
    width: glass.width,
    height: u * 2.4,
    fill: COLORS.divider,
    stroke: COLORS.divider,
    strokeWidth: u * 0.6,
  })
  addArrow(
    shapes,
    { x: glass.x + glass.width * 0.35, y: glass.y + glass.height * 0.30 },
    { x: glass.x + glass.width * 0.35, y: glass.y + glass.height * 0.15 },
    u,
  )
  addArrow(
    shapes,
    { x: glass.x + glass.width * 0.65, y: glass.y + glass.height * 0.70 },
    { x: glass.x + glass.width * 0.65, y: glass.y + glass.height * 0.85 },
    u,
  )
}

/**
 * Single hung: top sash fixed, bottom sash slides to open.
 * Divider in centre; arrow lives on the bottom pane only.
 */
function decorateSingleHung(shapes: DiagramShape[], glass: UnitBox, u: number) {
  const splitY = glass.y + glass.height / 2
  shapes.push({
    kind: 'rect',
    x: glass.x,
    y: splitY - u * 1.2,
    width: glass.width,
    height: u * 2.4,
    fill: COLORS.divider,
    stroke: COLORS.divider,
    strokeWidth: u * 0.6,
  })
  addArrow(
    shapes,
    { x: glass.x + glass.width * 0.5, y: glass.y + glass.height * 0.70 },
    { x: glass.x + glass.width * 0.5, y: glass.y + glass.height * 0.85 },
    u,
  )
}

/**
 * Single slider: left pane fixed, right pane slides leftward to open.
 * Mullion in centre; handles + arrow live on the right pane only.
 */
function decorateSingleSlider(shapes: DiagramShape[], glass: UnitBox, u: number) {
  const splitX = glass.x + glass.width / 2
  shapes.push({
    kind: 'rect',
    x: splitX - u * 1.2,
    y: glass.y,
    width: u * 2.4,
    height: glass.height,
    fill: COLORS.divider,
    stroke: COLORS.divider,
    strokeWidth: u * 0.6,
  })
  addHandle(shapes, splitX + u * 2.5, glass.y + glass.height / 2 - u * 8, u)
  addHandle(shapes, splitX + u * 2.5, glass.y + glass.height / 2 + u * 8, u)
  addArrow(
    shapes,
    { x: glass.x + glass.width * 0.70, y: glass.y + glass.height / 2 },
    { x: glass.x + glass.width * 0.55, y: glass.y + glass.height / 2 },
    u,
  )
}

function decorateDoubleSlider(shapes: DiagramShape[], glass: UnitBox, u: number) {
  const splitX = glass.x + glass.width / 2
  shapes.push({
    kind: 'rect',
    x: splitX - u * 1.2,
    y: glass.y,
    width: u * 2.4,
    height: glass.height,
    fill: COLORS.divider,
    stroke: COLORS.divider,
    strokeWidth: u * 0.6,
  })
  addHandle(shapes, splitX - u * 2.5, glass.y + glass.height / 2 - u * 8, u)
  addHandle(shapes, splitX - u * 2.5, glass.y + glass.height / 2 + u * 8, u)
  addArrow(
    shapes,
    { x: glass.x + glass.width * 0.30, y: glass.y + glass.height / 2 },
    { x: glass.x + glass.width * 0.45, y: glass.y + glass.height / 2 },
    u,
  )
}

function decorateAwning(shapes: DiagramShape[], glass: UnitBox, u: number) {
  const topCenter = { x: glass.x + glass.width / 2, y: glass.y }
  const bottomLeft = { x: glass.x, y: glass.y + glass.height }
  const bottomRight = { x: glass.x + glass.width, y: glass.y + glass.height }

  const stroke = COLORS.arrow
  const strokeWidth = u * 0.6
  shapes.push({ kind: 'line', from: bottomLeft, to: topCenter, stroke, strokeWidth })
  shapes.push({ kind: 'line', from: bottomRight, to: topCenter, stroke, strokeWidth })
  shapes.push({ kind: 'line', from: bottomLeft, to: bottomRight, stroke, strokeWidth })
}

function decorateTiltTurn(
  shapes: DiagramShape[],
  glass: UnitBox,
  u: number,
  hingeSide: 'left' | 'right',
) {
  decorateCasement(shapes, glass, u, hingeSide)
}

function decoratePatioDoor(shapes: DiagramShape[], glass: UnitBox, u: number) {
  decorateDoubleSlider(shapes, glass, u)
  shapes.push({
    kind: 'rect',
    x: glass.x + glass.width - u * 4,
    y: glass.y + glass.height / 2 - u * 14,
    width: u * 2,
    height: u * 28,
    fill: COLORS.hardware,
    stroke: COLORS.hardware,
    strokeWidth: u * 0.5,
  })
}

function applyDecoration(
  style: StyleEnum,
  shapes: DiagramShape[],
  glass: UnitBox,
  u: number,
  hingeSide?: 'left' | 'right',
) {
  switch (style) {
    case 'DH':    decorateDoubleHung(shapes, glass, u); break
    case 'SH':    decorateSingleHung(shapes, glass, u); break
    case 'SSL':   decorateSingleSlider(shapes, glass, u); break
    case 'DSL':   decorateDoubleSlider(shapes, glass, u); break
    case 'PD':    decoratePatioDoor(shapes, glass, u); break
    case 'AW':    decorateAwning(shapes, glass, u); break
    case 'CS':    decorateCasement(shapes, glass, u, hingeSide ?? 'right'); break
    case 'TT_HR': decorateTiltTurn(shapes, glass, u, 'right'); break
    case 'TT_HL': decorateTiltTurn(shapes, glass, u, 'left'); break
    case 'FIX':
    case 'PIC':   decorateFixed(shapes, glass, u); break
    default:      decorateFixed(shapes, glass, u); break
  }
}

/**
 * Emit shapes for a single window unit inside the given box.
 * Frame layers + glass-scoped decoration.
 */
export function buildUnitShapes(
  style: StyleEnum,
  box: UnitBox,
  hingeSide?: 'left' | 'right',
  frameColour: WindowColour = 'White',
): DiagramShape[] {
  const shapes: DiagramShape[] = []
  const u = Math.min(box.width, box.height) / 90
  const frameScale = style === 'PIC' ? PICTURE_FRAME_SCALE : 1
  pushFrameLayers(shapes, box, u, frameColour, frameScale)
  applyDecoration(style, shapes, glassRect(box, u, frameScale), u, hingeSide)
  return shapes
}

// ── Combination / single-item diagram ─────────────────────────────────────────

/**
 * Build a diagram for a quote item — single unit (1×1) or combination
 * (2×1 horizontal, or 1×2 vertical). A combination is two independent
 * windows joined by a mullion connector — each unit has its own full
 * frame whose thickness/colour reflects its own style and colour.
 */
export function buildCombinationDiagram(
  item: QuoteItem,
  maxWidth = DEFAULT_WIDTH,
  maxHeight = DEFAULT_HEIGHT,
): DiagramModel {
  const { width, height } = fitBox(maxWidth, maxHeight, itemAspectRatio(item))
  const shapes: DiagramShape[] = []
  const outerBox: UnitBox = { x: 0, y: 0, width, height }
  const u = Math.min(width, height) / 90
  const units = item.units
  const mullionThickness = u * MULLION_THICKNESS_U

  const frameScaleFor = (style: StyleEnum) =>
    style === 'PIC' ? PICTURE_FRAME_SCALE : 1

  const drawUnit = (unit: QuoteItemUnit, box: UnitBox) => {
    const unitFrameScale = frameScaleFor(unit.style)
    const unitFrameColour: WindowColour = unit.exteriorColour ?? 'White'
    pushFrameLayers(shapes, box, u, unitFrameColour, unitFrameScale)
    const unitGlass = glassRect(box, u, unitFrameScale)
    applyDecoration(unit.style, shapes, unitGlass, u, unit.hingeSide)
    shapes.push({
      kind: 'text',
      x: unitGlass.x + u * 3,
      y: unitGlass.y + u * 6,
      value: unit.id,
      color: COLORS.text,
      fontSize: u * 6,
    })
  }

  // Single unit: one frame around the whole diagram.
  if (units.length === 1) {
    drawUnit(units[0], outerBox)
    return { width, height, shapes }
  }

  // Combination: each unit is an independent window with its own frame.
  // A mullion connector sits between adjacent units. The connector uses the
  // first unit's exterior colour — the UI keeps unit colours in sync so this
  // matches both frames in practice.
  const isVertical = (item.configuration?.rows ?? 1) > 1
  const connectorColour: WindowColour = units[0]?.exteriorColour ?? 'White'
  const connectorPalette = FRAME_PALETTE[connectorColour]

  if (isVertical) {
    const totalRealHeight = units.reduce((sum, x) => sum + (x.height || 0), 0) || units.length
    const totalMullionSpace = mullionThickness * (units.length - 1)
    const availableHeight = Math.max(0, height - totalMullionSpace)

    const unitBoxes: UnitBox[] = []
    const mullionYs: number[] = []
    let cursorY = 0
    units.forEach((unit, idx) => {
      const share = (unit.height || 0) / totalRealHeight || 1 / units.length
      const unitHeight = availableHeight * share
      unitBoxes.push({ x: 0, y: cursorY, width, height: unitHeight })
      cursorY += unitHeight
      if (idx < units.length - 1) {
        mullionYs.push(cursorY)
        cursorY += mullionThickness
      }
    })

    unitBoxes.forEach((box, idx) => drawUnit(units[idx], box))

    for (const mullionY of mullionYs) {
      shapes.push({
        kind: 'rect',
        x: 0,
        y: mullionY,
        width,
        height: mullionThickness,
        fill: connectorPalette.outerFill,
        stroke: connectorPalette.outerStroke,
        strokeWidth: u * 1.4,
      })
    }
    return { width, height, shapes }
  }

  // Horizontal combination.
  const totalRealWidth = units.reduce((sum, x) => sum + (x.width || 0), 0) || units.length
  const totalMullionSpace = mullionThickness * (units.length - 1)
  const availableWidth = Math.max(0, width - totalMullionSpace)

  const unitBoxes: UnitBox[] = []
  const mullionXs: number[] = []
  let cursorX = 0
  units.forEach((unit, idx) => {
    const share = (unit.width || 0) / totalRealWidth || 1 / units.length
    const unitWidth = availableWidth * share
    unitBoxes.push({ x: cursorX, y: 0, width: unitWidth, height })
    cursorX += unitWidth
    if (idx < units.length - 1) {
      mullionXs.push(cursorX)
      cursorX += mullionThickness
    }
  })

  unitBoxes.forEach((box, idx) => drawUnit(units[idx], box))

  for (const mullionX of mullionXs) {
    shapes.push({
      kind: 'rect',
      x: mullionX,
      y: 0,
      width: mullionThickness,
      height,
      fill: connectorPalette.outerFill,
      stroke: connectorPalette.outerStroke,
      strokeWidth: u * 1.4,
    })
  }

  return { width, height, shapes }
}

// ── Rendering ─────────────────────────────────────────────────────────────────

function escapeXml(value: string): string {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;')
}

function hexToRgb(color: string) {
  const normalized = color.replace('#', '')
  if (normalized.length !== 6) return { r: 0, g: 0, b: 0 }

  return {
    r: Number.parseInt(normalized.slice(0, 2), 16),
    g: Number.parseInt(normalized.slice(2, 4), 16),
    b: Number.parseInt(normalized.slice(4, 6), 16),
  }
}

export function renderWindowSvg(
  item: QuoteItem,
  maxWidth = DEFAULT_WIDTH,
  maxHeight = DEFAULT_HEIGHT,
): string {
  const diagram = buildCombinationDiagram(item, maxWidth, maxHeight)

  const body = diagram.shapes
    .map((shape) => {
      switch (shape.kind) {
        case 'rect':
          return `<rect x="${shape.x}" y="${shape.y}" width="${shape.width}" height="${shape.height}" fill="${shape.fill ?? 'none'}" stroke="${shape.stroke ?? 'none'}" stroke-width="${shape.strokeWidth ?? 1}" />`
        case 'line':
          return `<line x1="${shape.from.x}" y1="${shape.from.y}" x2="${shape.to.x}" y2="${shape.to.y}" stroke="${shape.stroke ?? '#000'}" stroke-width="${shape.strokeWidth ?? 1}" stroke-linecap="round" />`
        case 'polyline':
          return `<polyline points="${shape.points.map((point) => `${point.x},${point.y}`).join(' ')}" fill="${shape.fill ?? 'none'}" stroke="${shape.stroke ?? '#000'}" stroke-width="${shape.strokeWidth ?? 1}" stroke-linecap="round" stroke-linejoin="round" />`
        case 'text':
          return `<text x="${shape.x}" y="${shape.y}" fill="${shape.color ?? COLORS.text}" font-size="${shape.fontSize ?? 6}" font-family="Helvetica, Arial, sans-serif" ${shape.bold ? 'font-weight="700"' : ''}>${escapeXml(shape.value)}</text>`
      }
    })
    .join('')

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${diagram.width} ${diagram.height}" width="${diagram.width}" height="${diagram.height}">${body}</svg>`
}

export function drawWindowDiagramPdf(
  doc: jsPDF,
  item: QuoteItem,
  x: number,
  y: number,
  maxWidth: number,
  maxHeight: number,
) {
  const diagram = buildCombinationDiagram(item, maxWidth, maxHeight)

  for (const shape of diagram.shapes) {
    switch (shape.kind) {
      case 'rect': {
        const hasFill = shape.fill && shape.fill !== 'none'
        const hasStroke = shape.stroke && shape.stroke !== 'none'
        if (hasFill) {
          const fill = hexToRgb(shape.fill!)
          doc.setFillColor(fill.r, fill.g, fill.b)
        }
        if (hasStroke) {
          const stroke = hexToRgb(shape.stroke!)
          doc.setDrawColor(stroke.r, stroke.g, stroke.b)
        }
        doc.setLineWidth(Math.max((shape.strokeWidth ?? 1) * 0.18, 0.006))
        const mode = hasFill && hasStroke ? 'FD' : hasFill ? 'F' : 'S'
        doc.rect(x + shape.x, y + shape.y, shape.width, shape.height, mode)
        break
      }
      case 'line': {
        const stroke = hexToRgb(shape.stroke ?? '#000000')
        doc.setDrawColor(stroke.r, stroke.g, stroke.b)
        doc.setLineWidth(Math.max((shape.strokeWidth ?? 1) * 0.18, 0.006))
        doc.line(x + shape.from.x, y + shape.from.y, x + shape.to.x, y + shape.to.y)
        break
      }
      case 'polyline': {
        const stroke = hexToRgb(shape.stroke ?? '#000000')
        doc.setDrawColor(stroke.r, stroke.g, stroke.b)
        doc.setLineWidth(Math.max((shape.strokeWidth ?? 1) * 0.18, 0.006))
        for (let index = 1; index < shape.points.length; index += 1) {
          const previous = shape.points[index - 1]
          const current = shape.points[index]
          doc.line(x + previous.x, y + previous.y, x + current.x, y + current.y)
        }
        break
      }
      case 'text': {
        doc.setFont('helvetica', shape.bold ? 'bold' : 'normal')
        doc.setFontSize(shape.fontSize ?? 6)
        const color = hexToRgb(shape.color ?? COLORS.text)
        doc.setTextColor(color.r, color.g, color.b)
        doc.text(shape.value, x + shape.x, y + shape.y, { baseline: 'top' })
        break
      }
    }
  }
}
