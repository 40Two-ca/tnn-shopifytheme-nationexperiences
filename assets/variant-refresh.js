import { StandardEvents } from '@shopify/events';

/**
 * Re-renders a custom block when the variant picker selects a different variant.
 *
 * Horizon only morphs the variant picker itself; every other block that depends
 * on the variant listens for the product select event and swaps in its own
 * counterpart from the fetched section, the way product-price.js does. This is
 * the generic version of that, for theme blocks that show variant-specific
 * content: wrap the block's markup in
 *
 *   <variant-refresh data-block-id="{{ block.id }}"> ... </variant-refresh>
 *
 * and it keeps itself up to date. The block id is what pairs the element on the
 * page with the one in the fetched HTML.
 */
class VariantRefresh extends HTMLElement {
  #section = null;

  connectedCallback() {
    this.#section = this.closest('.shopify-section, dialog');
    this.#section?.addEventListener(StandardEvents.productSelect, this.#handleProductSelect);
  }

  disconnectedCallback() {
    this.#section?.removeEventListener(StandardEvents.productSelect, this.#handleProductSelect);
    this.#section = null;
  }

  #handleProductSelect = (event) => {
    // Product cards run their own swatch flow and must not be touched here.
    if (!(event.target instanceof Element) || event.target.closest('product-card')) return;

    event.promise
      .then(({ detail }) => {
        const html = detail?.html;
        if (!html) return;

        const blockId = this.dataset.blockId;
        if (!blockId) return;

        const replacement = html.querySelector(`variant-refresh[data-block-id="${CSS.escape(blockId)}"]`);
        if (!replacement) return;

        this.innerHTML = replacement.innerHTML;
      })
      .catch((error) => {
        if (error?.name !== 'AbortError') console.warn('[variant-refresh] Event promise rejected:', error);
      });
  };
}

if (!customElements.get('variant-refresh')) {
  customElements.define('variant-refresh', VariantRefresh);
}
