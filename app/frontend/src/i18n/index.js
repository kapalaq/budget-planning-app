/**
 * Multi-language support for the budget planner frontend.
 *
 * JS port of app/languages/__init__.py — same JSON files,
 * same key format, same fallback logic.
 */

const DEFAULT_LANG = 'en-US';

const AVAILABLE_LANGUAGES = {
  'en-US': 'English (US)',
  'en-UK': 'English (UK)',
  'ru-RU': 'Русский',
};

// Eagerly import all locale JSON files from app/languages/.
// Vite resolves these at build time via glob import.
const localeModules = import.meta.glob('/../../languages/*.json', { eager: true });

// Build { "en-US": { "auth.title": "Budget Planner", ... }, ... }
const _LANGUAGES = {};

for (const [path, mod] of Object.entries(localeModules)) {
  // path looks like "/../../languages/en_US.json"
  const filename = path.split('/').pop();          // "en_US.json"
  const code = filename.replace('.json', '')        // "en_US"
                       .replace('_', '-');          // "en-US"
  _LANGUAGES[code] = mod.default || mod;
}

/**
 * Translate a key to the given language.
 *
 * Falls back to en-US if key not found in the requested language.
 * Falls back to the key itself if not found in any language.
 *
 * Supports {placeholder} substitution via params object.
 *
 * @param {string} key      - Dot-separated translation key, e.g. "auth.title"
 * @param {string} [lang]   - Language code, e.g. "ru-RU"
 * @param {Object} [params] - Placeholder values, e.g. { message: "oops" }
 * @returns {string}
 *
 * @example
 *   t('auth.title')                           // "Budget Planner"
 *   t('auth.error', 'en-US', { message: 'x' }) // "Error: x"
 */
function t(key, lang = DEFAULT_LANG, params = {}) {
  const strings = _LANGUAGES[lang] || {};
  let text = strings[key];

  // Fallback to default language
  if (text === undefined && lang !== DEFAULT_LANG) {
    text = (_LANGUAGES[DEFAULT_LANG] || {})[key];
  }

  // Fallback to key itself
  if (text === undefined) {
    text = key;
  }

  // Substitute {placeholder} tokens
  if (params && typeof params === 'object') {
    for (const [k, v] of Object.entries(params)) {
      text = text.replaceAll(`{${k}}`, String(v));
    }
  }

  return text;
}

export { AVAILABLE_LANGUAGES, DEFAULT_LANG, t };
export default t;
