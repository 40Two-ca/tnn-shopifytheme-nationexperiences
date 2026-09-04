/**
 * Trip finder search bar.
 *
 * Turns the Contiki-style "Where / What / When" bar into Shopify navigation:
 * - a destination alone goes straight to that collection
 * - a keyword and/or month (plus the destination name, if chosen) becomes a product search
 * - an empty form goes to the all-products collection
 */
class TripFinder extends HTMLElement {
  connectedCallback() {
    this.form = this.querySelector('form');
    this.form?.addEventListener('submit', this.handleSubmit);
    window.addEventListener('pageshow', this.reset);
  }

  disconnectedCallback() {
    this.form?.removeEventListener('submit', this.handleSubmit);
    window.removeEventListener('pageshow', this.reset);
  }

  /** Re-enable controls disabled during submit when the page is restored from the back/forward cache. */
  reset = () => {
    this.form?.querySelectorAll('[data-trip-finder-disabled]').forEach((element) => {
      element.disabled = false;
      element.removeAttribute('data-trip-finder-disabled');
    });
  };

  /** @param {SubmitEvent} event */
  handleSubmit = (event) => {
    const form = /** @type {HTMLFormElement} */ (event.currentTarget);
    const destination = /** @type {HTMLSelectElement | null} */ (form.querySelector('[name="destination"]'));
    const keywordInput = /** @type {HTMLInputElement | null} */ (form.querySelector('[name="q"]'));
    const when = /** @type {HTMLSelectElement | null} */ (form.querySelector('[name="when"]'));

    const keyword = keywordInput?.value.trim() ?? '';
    const month = when?.value ?? '';
    const destinationUrl = destination?.value ?? '';
    const destinationLabel = destination?.selectedOptions[0]?.dataset.label ?? '';

    if (!keyword && !month) {
      event.preventDefault();
      window.location.assign(destinationUrl || form.dataset.fallbackUrl || '/collections/all');
      return;
    }

    if (keywordInput) {
      keywordInput.value = [keyword, month, destinationLabel].filter(Boolean).join(' ');
    }

    for (const control of [destination, when]) {
      if (!control) continue;
      control.disabled = true;
      control.setAttribute('data-trip-finder-disabled', '');
    }
  };
}

if (!customElements.get('trip-finder')) {
  customElements.define('trip-finder', TripFinder);
}
