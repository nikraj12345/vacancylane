export type LocationOption = {
  id: string;
  label: string;
  type: "special" | "country" | "city";
  countryCode?: string;
};

export type LocationFilter = {
  label: string;
  city: string;
  state: string;
  country: string;
  remote: boolean;
};

const SPECIAL_LOCATIONS: LocationOption[] = [
  { id: "special:remote", label: "Remote", type: "special" },
  { id: "special:worldwide", label: "Worldwide", type: "special" },
  { id: "special:hybrid", label: "Hybrid", type: "special" },
];

/** Curated hiring hubs — always available without loading the full city DB. */
const POPULAR_LOCATIONS: LocationOption[] = [
  { id: "city:IN:Bengaluru", label: "Bengaluru, India", type: "city", countryCode: "IN" },
  { id: "city:IN:Hyderabad", label: "Hyderabad, India", type: "city", countryCode: "IN" },
  { id: "city:IN:Pune", label: "Pune, India", type: "city", countryCode: "IN" },
  { id: "city:IN:Mumbai", label: "Mumbai, India", type: "city", countryCode: "IN" },
  { id: "city:IN:Delhi", label: "Delhi, India", type: "city", countryCode: "IN" },
  { id: "city:IN:Gurugram", label: "Gurugram, India", type: "city", countryCode: "IN" },
  { id: "city:IN:Noida", label: "Noida, India", type: "city", countryCode: "IN" },
  { id: "city:IN:Chennai", label: "Chennai, India", type: "city", countryCode: "IN" },
  { id: "city:US:San Francisco", label: "San Francisco, United States", type: "city", countryCode: "US" },
  { id: "city:US:New York", label: "New York, United States", type: "city", countryCode: "US" },
  { id: "city:US:Seattle", label: "Seattle, United States", type: "city", countryCode: "US" },
  { id: "city:US:Austin", label: "Austin, United States", type: "city", countryCode: "US" },
  { id: "city:US:Boston", label: "Boston, United States", type: "city", countryCode: "US" },
  { id: "city:US:Chicago", label: "Chicago, United States", type: "city", countryCode: "US" },
  { id: "city:US:Los Angeles", label: "Los Angeles, United States", type: "city", countryCode: "US" },
  { id: "city:GB:London", label: "London, United Kingdom", type: "city", countryCode: "GB" },
  { id: "city:DE:Berlin", label: "Berlin, Germany", type: "city", countryCode: "DE" },
  { id: "city:CA:Toronto", label: "Toronto, Canada", type: "city", countryCode: "CA" },
  { id: "city:SG:Singapore", label: "Singapore, Singapore", type: "city", countryCode: "SG" },
  { id: "city:AE:Dubai", label: "Dubai, United Arab Emirates", type: "city", countryCode: "AE" },
  { id: "city:AU:Sydney", label: "Sydney, Australia", type: "city", countryCode: "AU" },
  { id: "city:NL:Amsterdam", label: "Amsterdam, Netherlands", type: "city", countryCode: "NL" },
  { id: "city:IE:Dublin", label: "Dublin, Ireland", type: "city", countryCode: "IE" },
];

type CscModule = typeof import("country-state-city");

let cscPromise: Promise<CscModule | null> | null = null;
let cachedCountries: LocationOption[] | null = null;

function loadCsc(): Promise<CscModule | null> {
  if (!cscPromise) {
    // The full city catalog is a large lazy chunk. If it fails to load the
    // picker stays usable on the curated list rather than taking down search.
    cscPromise = Promise.resolve()
      .then(() => import("country-state-city"))
      .catch((error) => {
        console.error("Location catalog failed to load", error);
        cscPromise = null;
        return null;
      });
  }
  return cscPromise;
}

export function getSpecialLocations(): LocationOption[] {
  return SPECIAL_LOCATIONS;
}

export function getPopularLocations(): LocationOption[] {
  return POPULAR_LOCATIONS;
}

export async function getAllCountries(): Promise<LocationOption[]> {
  if (cachedCountries) return cachedCountries;
  const csc = await loadCsc();
  if (!csc) return [];
  cachedCountries = csc.Country.getAllCountries()
    .map((country) => ({
      id: `country:${country.isoCode}`,
      label: country.name,
      type: "country" as const,
      countryCode: country.isoCode,
    }))
    .sort((a, b) => a.label.localeCompare(b.label));
  return cachedCountries;
}

/**
 * Sync quick search for empty/popular queries.
 * Full country+city search is async via `searchLocationsAsync`.
 */
export function searchLocations(query: string, limit = 40): LocationOption[] {
  const q = query.trim().toLowerCase();
  const base = [...SPECIAL_LOCATIONS, ...POPULAR_LOCATIONS];
  if (!q) return base.slice(0, limit);
  return base
    .filter((option) => option.label.toLowerCase().includes(q))
    .slice(0, limit);
}

/** Full searchable catalog (countries + cities) via country-state-city. */
export async function searchLocationsAsync(
  query: string,
  limit = 50
): Promise<LocationOption[]> {
  const q = query.trim().toLowerCase();
  if (!q) return searchLocations("", limit);

  const results: LocationOption[] = [];
  const seen = new Set<string>();
  const push = (option: LocationOption) => {
    if (seen.has(option.id) || results.length >= limit) return;
    seen.add(option.id);
    results.push(option);
  };

  for (const option of searchLocations(q, limit)) {
    push(option);
  }

  const csc = await loadCsc();
  if (!csc) return results;
  const { City, Country } = csc;
  const countries = Country.getAllCountries().filter((country) =>
    country.name.toLowerCase().includes(q)
  );

  for (const country of countries.slice(0, 12)) {
    push({
      id: `country:${country.isoCode}`,
      label: country.name,
      type: "country",
      countryCode: country.isoCode,
    });
  }

  const countryCodes = new Set(
    countries.slice(0, 8).map((country) => country.isoCode)
  );
  for (const code of ["US", "IN", "GB", "CA", "DE", "AU", "SG", "AE", "NL", "IE"]) {
    countryCodes.add(code);
  }

  for (const code of countryCodes) {
    const countryName = Country.getCountryByCode(code)?.name || code;
    for (const city of City.getCitiesOfCountry(code) || []) {
      if (!city.name.toLowerCase().includes(q)) continue;
      push({
        id: `city:${code}:${city.name}`,
        label: `${city.name}, ${countryName}`,
        type: "city",
        countryCode: code,
      });
      if (results.length >= limit) break;
    }
    if (results.length >= limit) break;
  }

  return results;
}

/** Convert selected locations into a search-engine friendly location clause. */
export function locationsToQueryClause(locations: LocationOption[]): string {
  if (!locations.length) return "";
  const terms = locations.map((location) => {
    if (location.type === "city") {
      const city = location.label.split(",")[0]?.trim() || location.label;
      return `"${city}"`;
    }
    return `"${location.label}"`;
  });
  if (terms.length === 1) return terms[0];
  return `(${terms.join(" OR ")})`;
}

export function locationLabels(locations: LocationOption[]): string {
  return locations.map((location) => location.label).join(", ");
}

/** Map resume-parser locations onto the dropdown's LocationOption shape. */
export function resumeLocationsToOptions(
  locations: Array<{
    label: string;
    city?: string;
    state?: string;
    country?: string;
    remote?: boolean;
  }>
): LocationOption[] {
  const options: LocationOption[] = [];
  const seen = new Set<string>();
  for (const location of locations) {
    if (location.remote) {
      const remote = SPECIAL_LOCATIONS[0];
      if (!seen.has(remote.id)) {
        seen.add(remote.id);
        options.push(remote);
      }
      continue;
    }
    const popular = POPULAR_LOCATIONS.find((option) => {
      const city = option.label.split(",")[0]?.trim().toLowerCase();
      return (
        city === (location.city || location.label).toLowerCase() ||
        option.label.toLowerCase() === location.label.toLowerCase()
      );
    });
    if (popular && !seen.has(popular.id)) {
      seen.add(popular.id);
      options.push(popular);
      continue;
    }
    if (location.city) {
      const id = `city:resume:${location.city}`;
      if (!seen.has(id)) {
        seen.add(id);
        options.push({
          id,
          label: location.country
            ? `${location.city}, ${location.country}`
            : location.city,
          type: "city",
        });
      }
      continue;
    }
    if (location.country) {
      const id = `country:resume:${location.country}`;
      if (!seen.has(id)) {
        seen.add(id);
        options.push({
          id,
          label: location.country,
          type: "country",
        });
      }
    }
  }
  return options;
}

/**
 * Structured form of each selection, so the backend can match a posting's real
 * location instead of guessing from the search clause.
 */
export function locationsToFilters(
  locations: LocationOption[]
): LocationFilter[] {
  return locations.map((location) => {
    const [first, ...rest] = location.label.split(",").map((part) => part.trim());
    if (location.type === "city") {
      return {
        label: location.label,
        city: first || "",
        state: "",
        country: rest.join(", "),
        remote: false,
      };
    }
    if (location.type === "country") {
      return {
        label: location.label,
        city: "",
        state: "",
        country: location.label,
        remote: false,
      };
    }
    return {
      label: location.label,
      city: "",
      state: "",
      country: "",
      remote: location.label.toLowerCase() !== "hybrid",
    };
  });
}
