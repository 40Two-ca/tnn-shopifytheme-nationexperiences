/**
 * Trip finder search bar.
 *
 * Three text boxes (where / what / when) become Shopify navigation:
 * - a destination that matches a collection name (with nothing else typed) goes to that collection
 * - otherwise every non-empty box is joined into one product search
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

  /**
   * Find the collection URL whose title matches the typed destination.
   * @param {HTMLInputElement | null} input
   */
  matchingCollectionUrl(input) {
    if (!input?.list) return '';
    const typed = input.value.trim().toLowerCase();
    if (!typed) return '';
    const option = Array.from(input.list.options).find((item) => item.value.trim().toLowerCase() === typed);
    return option?.dataset.url ?? '';
  }

  /** @param {SubmitEvent} event */
  handleSubmit = (event) => {
    const form = /** @type {HTMLFormElement} */ (event.currentTarget);
    const destination = /** @type {HTMLInputElement | null} */ (form.querySelector('[name="destination"]'));
    const keywordInput = /** @type {HTMLInputElement | null} */ (form.querySelector('[name="q"]'));
    const when = /** @type {HTMLInputElement | null} */ (form.querySelector('[name="when"]'));

    const where = destination?.value.trim() ?? '';
    const keyword = keywordInput?.value.trim() ?? '';
    const month = when?.value.trim() ?? '';
    const collectionUrl = this.matchingCollectionUrl(destination);

    if (!keyword && !month && (collectionUrl || !where)) {
      event.preventDefault();
      window.location.assign(collectionUrl || form.dataset.fallbackUrl || '/collections/all');
      return;
    }

    if (keywordInput) {
      keywordInput.value = [keyword, month, where].filter(Boolean).join(' ');
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
