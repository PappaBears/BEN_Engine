// PROPOSAL panel: the selector is the input; one click produces the customer proposal and the deal packages.
import { api, h } from '../util.js';

let out = null, optSel = null, custIn = null, siteIn = null, stateIn = null, busy = false;

export default {
  id: 'proposal', label: 'Proposal', title: 'Proposal and deal package',
  async mount(el) {
    optSel = h('select', {});
    try { const o = await api('/api/proposal/options'); for (const k of o.options) optSel.append(h('option', { value: k, selected: k === o.default }, label(k))); }
    catch (e) { optSel.append(h('option', { value: 'hardware_controls' }, 'Hardware + BEN Controls')); }
    custIn = h('input', { type: 'text', value: 'Customer', maxlength: 80 });
    siteIn = h('input', { type: 'text', value: 'Site', maxlength: 120 });
    stateIn = h('input', { type: 'text', value: '', placeholder: 'Governing state (contracts)', maxlength: 40 });
    out = h('div', { class: 'note' }, 'Set the configuration in the Selector, then generate. Every number in the proposal comes from the current configuration, the bill of materials and the compliance pack.');
    el.append(
      h('h3', {}, 'Deal inputs'),
      h('div', { class: 'field' }, h('label', {}, 'Purchase option'), optSel),
      h('div', { class: 'field' }, h('label', {}, 'Customer'), custIn),
      h('div', { class: 'field' }, h('label', {}, 'Site'), siteIn),
      h('div', { class: 'field' }, h('label', {}, 'Governing state'), stateIn),
      h('div', { class: 'row' },
        h('button', { class: 'btn btn-primary', id: 'btn-proposal', onClick: () => run('proposal') }, 'Generate proposal'),
        h('button', { class: 'btn', id: 'btn-package', onClick: () => run('package') }, 'Build deal packages')),
      h('h3', {}, 'Result'), out,
      h('p', { class: 'muted', style: { fontSize: '12px' } }, 'The proposal is 16 sections: scope, price by option with the confirmed/list/estimate split, schedule from the process flow and lead times, drawings, compliance pack, risks before price, site requirements, acceptance, terms. The packages add the pre-filled SOW, change order and acceptance certificates (customer) and the integrator / contract-manufacturing / supplier terms with the SQAM (partner).'),
    );
  },
  update() {},
};

function usd(v) { return v == null ? '–' : '$' + Math.round(v).toLocaleString('en-US'); }
function label(k) { return { hardware_only: 'Hardware only', hardware_controls: 'Hardware + BEN Controls', white_label: 'White-label', managed: 'Managed service', modules: 'Selected modules only' }[k] || k; }

async function run(kind) {
  if (busy) return; busy = true;
  out.replaceChildren(h('div', { class: 'muted' }, kind === 'proposal' ? 'Building proposal…' : 'Assembling packages (copies drawings; may take a few seconds)…'));
  try {
    const body = { option: optSel.value, customer: custIn.value, site: siteIn.value };
    if (kind === 'proposal') {
      const r = await api('/api/proposal', { body });
      const rows = (r.prices || []).map(p => h('tr', {}, h('td', {}, p.label || p.key || ''), h('td', {}, usd(p.capital_price_usd)), h('td', {}, p.recurring_usd_per_year ? usd(p.recurring_usd_per_year) + '/yr' : '–')));
      out.replaceChildren(
        h('div', {}, h('strong', {}, r.proposal_id), ' · ', r.customer, ' · ', r.site),
        rows.length ? h('table', { class: 'kv' }, h('thead', {}, h('tr', {}, h('th', {}, 'Option'), h('th', {}, 'Capital'), h('th', {}, 'Recurring'))), h('tbody', {}, ...rows)) : null,
        h('div', { class: 'row' },
          h('a', { class: 'btn btn-primary', href: r.html_url, target: '_blank', rel: 'noopener' }, 'Open proposal (HTML)'),
          h('a', { class: 'btn', href: r.md_url, download: r.proposal_id + '.md' }, 'Markdown'),
          h('a', { class: 'btn', href: r.json_url, download: r.proposal_id + '.json' }, 'JSON')));
    } else {
      body.fields = stateIn.value ? { GOVERNING_STATE: stateIn.value } : {};
      const r = await api('/api/package', { body });
      out.replaceChildren(
        h('div', {}, h('strong', {}, 'Packages built')),
        ...['customer', 'partner'].filter(k => r[k]).map(k => h('div', { class: 'field' }, h('div', {}, k === 'customer' ? 'Customer deal package' : 'Partner (integrator / CM) package', ' · ', r[k].summary), h('a', { class: 'btn', href: r[k].zip_url }, 'Download zip'))));
    }
  } catch (e) { out.replaceChildren(h('div', { class: 'error' }, e.message)); }
  busy = false;
}
