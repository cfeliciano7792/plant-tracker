import { useEffect, useRef, useState } from "react";
import { searchExternalSpecies, searchLocalSpecies } from "../api/plantSearch";

export default function PlantSearchAutocomplete({ onSelectExisting, onSelectCandidate, onManual }) {
  const [query, setQuery] = useState("");
  const [localResults, setLocalResults] = useState([]);
  const [externalResults, setExternalResults] = useState(null);
  const [searchedExternal, setSearchedExternal] = useState(false);
  const [loadingExternal, setLoadingExternal] = useState(false);
  const [error, setError] = useState(null);
  const debounceRef = useRef(null);

  useEffect(() => {
    setExternalResults(null);
    setSearchedExternal(false);
    setError(null);

    if (query.trim().length < 2) {
      setLocalResults([]);
      return;
    }

    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        const results = await searchLocalSpecies(query.trim());
        setLocalResults(results);
      } catch (err) {
        setError(err.message);
      }
    }, 300);

    return () => clearTimeout(debounceRef.current);
  }, [query]);

  const handleSearchOnline = async () => {
    setLoadingExternal(true);
    setError(null);
    try {
      const results = await searchExternalSpecies(query.trim());
      setExternalResults(results);
      setSearchedExternal(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingExternal(false);
    }
  };

  return (
    <div className="plant-search">
      <label>
        Search for a plant
        <input
          type="text"
          placeholder="e.g. Golden Pothos"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </label>

      {error && <p className="error">{error}</p>}

      {localResults.length > 0 && (
        <ul className="search-results">
          {localResults.map((species) => (
            <li key={species.id}>
              <button type="button" onClick={() => onSelectExisting(species)}>
                <strong>{species.common_name}</strong>
                {species.scientific_name && <em> — {species.scientific_name}</em>}
                <span className="tag">already in your family's collection</span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {query.trim().length >= 2 && localResults.length === 0 && !searchedExternal && (
        <button type="button" onClick={handleSearchOnline} disabled={loadingExternal}>
          {loadingExternal ? "Searching..." : "Can't find it? Search the plant database online"}
        </button>
      )}

      {externalResults && externalResults.length > 0 && (
        <ul className="search-results">
          {externalResults.map((candidate, i) => (
            <li key={i}>
              <button type="button" onClick={() => onSelectCandidate(candidate)}>
                <strong>{candidate.common_name}</strong>
                {candidate.scientific_name && <em> — {candidate.scientific_name}</em>}
                <span className="tag">from {candidate.data_source}</span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {externalResults && externalResults.length === 0 && (
        <p className="hint">No matches found online either.</p>
      )}

      <p>
        <button type="button" onClick={onManual}>
          Enter it manually instead
        </button>
      </p>
    </div>
  );
}
