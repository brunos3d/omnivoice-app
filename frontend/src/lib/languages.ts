// Centralized language registry. The full list is generated from OmniVoice's
// languages.md (see languages.generated.ts + scripts/generate-languages.mjs) and must
// never be hand-maintained. This module adds the small, curated overlay: common-language
// ordering, flags, and lookup/search helpers.

import { GENERATED_LANGUAGES } from "./languages.generated";

export interface SupportedLanguage {
  /** OmniVoice language ID — the value sent to the model's generate(language=...). */
  id: string;
  name: string;
  /** ISO 639-3 code (metadata). */
  isoCode: string;
  trainingHours?: number;
  /** Curated, optional — most of the 646 languages have none. */
  flag?: string;
}

/** Curated short list surfaced in the "Common" group, in display order. */
export const COMMON_LANGUAGE_IDS = [
  "en",
  "es",
  "pt",
  "fr",
  "de",
  "it",
  "ru",
  "zh",
  "ja",
  "ko",
  "hi",
  "arb",
] as const;

/** Best-effort representative flags for common languages (languages ≠ countries). */
export const LANGUAGE_FLAGS: Record<string, string> = {
  en: "🇬🇧",
  es: "🇪🇸",
  pt: "🇧🇷",
  fr: "🇫🇷",
  de: "🇩🇪",
  it: "🇮🇹",
  ru: "🇷🇺",
  zh: "🇨🇳",
  ja: "🇯🇵",
  ko: "🇰🇷",
  hi: "🇮🇳",
  arb: "🇸🇦",
};

/**
 * Locale-specific overlay for provider codes that don't match the OmniVoice registry.
 * Kokoro (and any other locale-aware provider) uses BCP-47 style codes like "en-us"
 * and "en-gb" instead of the family-level "en". Each entry provides a display
 * ``name`` and ``flag`` so the combobox can render consistently across providers.
 */
export const LOCALE_LANGUAGE_OVERLAY: Record<string, SupportedLanguage> = {
  "en-us": { id: "en-us", name: "English (US)", isoCode: "eng", flag: "🇺🇸" },
  "en-gb": { id: "en-gb", name: "English (UK)", isoCode: "eng", flag: "🇬🇧" },
  "es-es": { id: "es-es", name: "Spanish (Spain)", isoCode: "spa", flag: "🇪🇸" },
  "es-mx": { id: "es-mx", name: "Spanish (Mexico)", isoCode: "spa", flag: "🇲🇽" },
  "pt-br": { id: "pt-br", name: "Portuguese (Brazil)", isoCode: "por", flag: "🇧🇷" },
  "pt-pt": { id: "pt-pt", name: "Portuguese (Portugal)", isoCode: "por", flag: "🇵🇹" },
  "fr-fr": { id: "fr-fr", name: "French (France)", isoCode: "fra", flag: "🇫🇷" },
  "fr-ca": { id: "fr-ca", name: "French (Canada)", isoCode: "fra", flag: "🇨🇦" },
  "zh-cn": { id: "zh-cn", name: "Chinese (Simplified)", isoCode: "zho", flag: "🇨🇳" },
  "zh-tw": { id: "zh-tw", name: "Chinese (Traditional)", isoCode: "zho", flag: "🇹🇼" },
};

export const SUPPORTED_LANGUAGES: SupportedLanguage[] = GENERATED_LANGUAGES.map(
  (l) => ({
    ...l,
    flag: LANGUAGE_FLAGS[l.id],
  }),
);

const BY_ID = new Map(SUPPORTED_LANGUAGES.map((l) => [l.id, l]));
const BY_NAME = new Map(
  SUPPORTED_LANGUAGES.map((l) => [l.name.toLowerCase(), l]),
);

export function getLanguageById(
  id: string | null | undefined,
): SupportedLanguage | undefined {
  if (!id) return undefined
  // Locale overlay first — covers Kokoro-style BCP-47 codes.
  const overlaid = LOCALE_LANGUAGE_OVERLAY[id]
  if (overlaid) return overlaid
  return BY_ID.get(id)
}

export function getLanguageByName(
  name: string | null | undefined,
): SupportedLanguage | undefined {
  return name ? BY_NAME.get(name.toLowerCase()) : undefined;
}

/**
 * Resolve a stored value to a display label. Accepts either an OmniVoice id (current)
 * or a legacy display name (older voices), falling back to the raw value, then "Auto".
 */
export function getLanguageLabel(value: string | null | undefined): string {
  if (!value) return "Auto";
  return (getLanguageById(value) ?? getLanguageByName(value))?.name ?? value;
}

export const COMMON_LANGUAGES: SupportedLanguage[] = COMMON_LANGUAGE_IDS.map(
  (id) => BY_ID.get(id),
).filter((l): l is SupportedLanguage => Boolean(l));

export const ALL_LANGUAGES_SORTED: SupportedLanguage[] = [
  ...SUPPORTED_LANGUAGES,
].sort((a, b) => a.name.localeCompare(b.name));

/** Simple substring search across name, OmniVoice id, and ISO code. */
export function searchLanguages(query: string): SupportedLanguage[] {
  const q = query.trim().toLowerCase();
  if (!q) return ALL_LANGUAGES_SORTED;
  return ALL_LANGUAGES_SORTED.filter(
    (l) =>
      l.name.toLowerCase().includes(q) ||
      l.id.toLowerCase().includes(q) ||
      l.isoCode.toLowerCase().includes(q),
  );
}

/**
 * Unified display string: ``flag name (code)``. Falls back to just the raw value
 * (or "Auto") when the language cannot be resolved. Used by the combobox trigger
 * and any card/list renderer that wants consistent label across providers.
 */
export function formatLanguage(
  value: string | null | undefined,
): string {
  if (!value) return "Auto"
  const lang = getLanguageById(value)
  if (!lang) return value
  const flag = lang.flag ? `${lang.flag} ` : ""
  return `${flag}${lang.name} (${lang.id})`
}
