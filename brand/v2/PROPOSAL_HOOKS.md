# Proposal HTML: brand v2 hooks (for the lead to apply in `software/ben_engine/proposal.py`)

The brand agent did not edit `proposal.py` (owned by the lineup work). `to_html()` keeps working today: `web/kit/brand.json` keeps every key it reads (`brand`, `product`, `tagline`, `colors.graphite/slate/panel/text/muted/cyan/amber/red/green/light_bg/light_text`, `type.display/mono`) and those keys now carry v2 values. `tests/test_proposal.py::test_markdown_and_html_render` still passes because the literal `#66E3FF`/`#0B1018` it checks come from `_LOGO_SVG`; that assertion has to change when step 2 below lands (assert `#1E40AF` and `#06101F` instead).

Apply in this order:

1. **Stylesheet.** Append `brand/v2/proposal.css` after the generated `<style>` in `to_html()`, inlined (proposals travel as one file):
   `css += (REPO_ROOT / "brand/v2/proposal.css").read_text()` with the `@import` line removed, and the fonts inlined as data URIs (same five WOFF2 files `scripts/brand_deck.py` embeds: `FONTS` list there; reuse `font_css()`).
2. **Logo.** Replace `_LOGO_SVG` (Rev 1 SAI monogram) with the v2 horizontal lockup on white: the contents of `brand/v2/lockup-deep.svg`, given `class="sai-lockup"` and `height="34"` on the root `<svg>`. Never redraw it. For a white-label proposal keep the partner name in the eyebrow and put the lockup in the "engineering by" line.
3. **Header eyebrow.** `"{brand} · BEN Engine · Proposal {id}"` → `"BEN Engine, by Schreiber AI · Proposal {id} · Rev 2"` (white-label: `"{partner} · BEN Engine · engineering by Schreiber AI · Proposal {id}"`).
4. **Page footer = data plate band.** Replace the `.pf` content with
   `<footer class='pf'><b>Schreiber AI</b><i></i><span>Proposal {id}</span><i></i><span>{tier_label}</span><i></i><span>Rated {it_kw_max} kW IT</span><span class='grow'></span><span>{n} / {total}</span></footer>`
   (the package's proposal band: `Proposal · SA-2026-0012 · Rated: 3 weeks · Page 2 / 6`). `.pf` is shown in print by `proposal.css`.
5. **Legal line** on the last page (signature section) and on the cover under the sub-line: `<p class='legal'>Schreiber AI is a Schreiber Holding LLC company.</p>`.
6. **Proof slots.** Where a number is not yet measured or quoted (BEN 1 / BEN 300 / BEN 1000 prices, pilot results), print `<span class='pending'>fact pending</span>` instead of a value; never an estimate dressed as a fact.
7. **One amber per document.** The acceptance/sign call to action, if rendered as a link, gets `class='cta-primary'`. Nothing else is amber; the proposed option row (`td.hl`) is bold Ink with a cobalt rule.
8. **Colors in text.** `#0A6B86` and `#8A5A00` in the Rev 1 print block are superseded by `proposal.css` (Deep Cobalt `#1E40AF` for accents, Ink for emphasis).

Classes `proposal.css` styles: `.wrap`, `nav.toc`, `.page`, `.page.cover`, `.hdr`, `.hdr .sai-lockup`, `.eyebrow`, `h1`, `.sub`, `h2 .n`, `.tw`, `table`, `thead th`, `td.num`, `td.hl`, `table.kv`, `.pf` (+ `b`, `i`, `.grow`), `.wm`, `.legal`, `.pending`, `.cta-primary`, `code`.
