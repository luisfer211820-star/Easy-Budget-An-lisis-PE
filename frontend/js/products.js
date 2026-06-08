// ─────────────────────────────────────────────
// EasyBudget — Products & Analysis Module (API-based + SQLite)
// Sprint 4: added stock field + updateStock()
// ─────────────────────────────────────────────
import { getSession } from './auth.js';

const API_BASE = 'http://localhost:5000/api';

/* ── CRUD (async — calls backend API) ── */
export async function getProducts() {
  const session = getSession();
  if (!session) return [];
  try {
    const res = await fetch(`${API_BASE}/products?user_id=${session.id}`);
    const data = await res.json();
    return data.products || [];
  } catch (err) {
    console.error('Error fetching products:', err);
    return [];
  }
}

export async function getDeletedProducts() {
  const session = getSession();
  if (!session) return [];
  try {
    const res = await fetch(`${API_BASE}/products/deleted?user_id=${session.id}`);
    const data = await res.json();
    return data.products || [];
  } catch (err) {
    console.error('Error fetching deleted products:', err);
    return [];
  }
}

export async function getProductById(id) {
  try {
    const res = await fetch(`${API_BASE}/products/${id}`);
    const data = await res.json();
    return data.product || null;
  } catch (err) {
    console.error('Error fetching product:', err);
    return null;
  }
}

export async function saveProduct(data) {
  const session = getSession();
  try {
    const res = await fetch(`${API_BASE}/products`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: session.id,
        name: data.name,
        fixedCost: data.fixedCost,
        variableCost: data.variableCost,
        salePrice: data.salePrice,
        forecastUnits: data.forecastUnits,
        stock: data.stock ?? 0,
      })
    });
    const result = await res.json();
    return result.product || null;
  } catch (err) {
    console.error('Error saving product:', err);
    return null;
  }
}

export async function updateProduct(id, data) {
  try {
    const res = await fetch(`${API_BASE}/products/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: data.name,
        fixedCost: data.fixedCost,
        variableCost: data.variableCost,
        salePrice: data.salePrice,
        forecastUnits: data.forecastUnits,
        stock: data.stock ?? 0,
      })
    });
    const result = await res.json();
    return result.product || null;
  } catch (err) {
    console.error('Error updating product:', err);
    return null;
  }
}

export async function updateStock(id, stock) {
  try {
    const res = await fetch(`${API_BASE}/products/${id}/stock`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stock })
    });
    const result = await res.json();
    return result.product || null;
  } catch (err) {
    console.error('Error updating stock:', err);
    return null;
  }
}

export async function deleteProduct(id) {
  try {
    await fetch(`${API_BASE}/products/${id}`, { method: 'DELETE' });
  } catch (err) {
    console.error('Error deleting product:', err);
  }
}

export async function restoreProduct(id) {
  try {
    const res = await fetch(`${API_BASE}/products/${id}/restore`, { method: 'POST' });
    const result = await res.json();
    return result.ok || false;
  } catch (err) {
    console.error('Error restoring product:', err);
    return false;
  }
}

/* ── Financial Analysis (runs client-side) ── */
export function analyzeProduct(product) {
  const { fixedCost, variableCost, salePrice } = product;
  const contribution = salePrice - variableCost;
  const marginPct = ((contribution / salePrice) * 100);

  // Break-even
  const peUnits = contribution > 0 ? Math.ceil(fixedCost / contribution) : Infinity;
  const peMoney = peUnits * salePrice;

  // Scenario table: 0 to 2× PE (20 steps)
  const scenarios = [];
  const maxUnits = peUnits === Infinity ? 100 : peUnits * 2;
  const steps = 16;
  for (let i = 0; i <= steps; i++) {
    const units = Math.round((maxUnits / steps) * i);
    const revenue = units * salePrice;
    const totalCost = fixedCost + units * variableCost;
    const profit = revenue - totalCost;
    scenarios.push({ units, revenue, totalCost, profit });
  }

  // Recommendation
  let recommendation, recLevel;
  if (marginPct > 40) {
    recommendation = '📈 Producto de alta rentabilidad — aumenta inventario y considera expandir el mercado.';
    recLevel = 'high';
  } else if (marginPct >= 20) {
    recommendation = '⚖️ Rentabilidad media — optimiza costos variables para mejorar el margen.';
    recLevel = 'medium';
  } else {
    recommendation = '⚠️ Margen bajo — revisa el precio de venta o reduce costos fijos urgentemente.';
    recLevel = 'low';
  }

  return { contribution, marginPct, peUnits, peMoney, scenarios, recommendation, recLevel };
}

/* ── Multi-Product Analysis ── */
export function analyzeMultiEquilibrium(fixedCost, products) {
  if (!products || products.length < 2) {
    return { error: 'Agrega al menos 2 productos para el análisis multiproducto' };
  }
  if (fixedCost <= 0) {
    return { error: 'El costo fijo debe ser mayor a 0' };
  }

  let totalForecastUnits = 0;
  for (const p of products) {
    if (!p.forecastUnits || p.forecastUnits <= 0) return { error: `Las unidades pronosticadas para ${p.name} deben ser mayores a 0` };
    totalForecastUnits += p.forecastUnits;
  }

  let validationParticipationSum = 0;
  let totalCMP = 0;
  let hasNegativeCMU = false;
  const analysisProducts = [];

  for (const p of products) {
    const cmu = p.salePrice - p.variableCost;
    if (cmu < 0) hasNegativeCMU = true;

    const participation = p.forecastUnits / totalForecastUnits;
    validationParticipationSum += participation;

    const cmp = cmu * participation;
    totalCMP += cmp;

    analysisProducts.push({
      id: p.id,
      name: p.name,
      salePrice: p.salePrice,
      cmu,
      participation,
      participationPct: (participation * 100).toFixed(1) + '%',
      cmp
    });
  }

  if (Math.abs(validationParticipationSum - 1.0) > 0.001) {
    return { error: 'La sumatoria de participaciones debe ser 100%' };
  }

  const peGeneralUnits = Math.ceil(fixedCost / totalCMP);

  for (const ap of analysisProducts) {
    ap.peUnits = Math.ceil(peGeneralUnits * ap.participation);
    ap.pePesos = ap.peUnits * ap.salePrice;
    delete ap.salePrice;
  }

  return {
    peGeneralUnits,
    products: analysisProducts,
    summary: {
      totalFixedCost: fixedCost,
      totalCmp: totalCMP,
      totalForecastUnits: totalForecastUnits,
      validationParticipationSum: 1.0
    },
    warning: hasNegativeCMU ? '⚠️ Advertencia: Un producto está vendiendo a pérdida (CMU negativo).' : null
  };
}

/* ── Inventory Analysis (Sprint 4 — HU014 & HU015) ── */
export function analyzeInventory(products) {
  return products.map(p => {
    const cmu = p.salePrice - p.variableCost;
    const marginPct = p.salePrice > 0 ? (cmu / p.salePrice) * 100 : 0;
    const peUnits = cmu > 0 ? Math.ceil(p.fixedCost / cmu) : Infinity;
    const stock = p.stock ?? 0;
    const gap = isFinite(peUnits) ? peUnits - stock : null;
    const status = !isFinite(peUnits) ? 'danger'
      : stock >= peUnits ? 'ok'
      : stock >= peUnits * 0.75 ? 'warning'
      : 'danger';

    let priority, priorityLabel;
    if (marginPct > 40) { priority = 3; priorityLabel = 'Alta'; }
    else if (marginPct >= 20) { priority = 2; priorityLabel = 'Media'; }
    else { priority = 1; priorityLabel = 'Baja'; }

    return { ...p, cmu, marginPct, peUnits, stock, gap, status, priority, priorityLabel };
  });
}

/* ── Format helpers ── */
export function fmt(n, currency = true) {
  if (!isFinite(n)) return '—';
  return currency
    ? '$' + n.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
    : n.toLocaleString('es-CO', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
}

/* ── CSV Export ── */
export function downloadCSV(product, analysis) {
  const { scenarios } = analysis;
  const headers = ['Unidades Vendidas', 'Ingresos', 'Costo Total', 'Utilidad'];
  const rows = scenarios.map(s => [s.units, s.revenue, s.totalCost, s.profit]);
  const csv = [
    `# Análisis de Punto de Equilibrio — ${product.name}`,
    `# Margen de Contribución: $${analysis.contribution} (${analysis.marginPct.toFixed(1)}%)`,
    `# Punto de Equilibrio: ${analysis.peUnits} unidades / $${analysis.peMoney}`,
    '',
    headers.join(','),
    ...rows.map(r => r.join(','))
  ].join('\n');

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `easybudget_${product.name.replace(/\s+/g, '_')}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
