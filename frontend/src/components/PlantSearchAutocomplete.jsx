import { useEffect, useRef, useState } from "react";
import { searchExternalSpecies, searchLocalSpecies } from "../api/plantSearch";

const LOCAL_DEBOUNCE_MS = 200;
const EXTERNAL_DEBOUNCE_MS = 600;

export default function PlantSearchAutocomplete({ onSelectExisting, onSelectCandidate, onManual }) {
  const [query, setQuery] = useState("");
  const [localResults, setLocalResults] = useState([]);
  const [externalResults, setExternalResults] = useState(null);
  const [loadingExternal, setLoadingExternal] = useState(false);
  const [error, setError] = useState(null);
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);

  const localDebounceRef = useRef(null);
  const externalDebounceRef = useRef(null);
  const containerRef = useRef(null);

  const results = localResults.length > 0 ? localResults : externalResults || [];

  useEffect(() => {
    setExternalResults(null);
    setError(null);
    setHighlightedIndex(-1);
    clearTimeout(externalDebounceRef.current);

    if (query.trim().length < 2) {
      setLocalResults([]);
      setIsOpen(false);
      return;
    }

    setIsOpen(true);
    clearTimeout(localDebounceRef.current);
    localDebounceRef.current = setTimeout(async () => {
      try {
        const local = await searchLocalSpecies(query.trim());
        setLocalResults(local);

        if (local.length === 0) {
          externalDebounceRef.current = setTimeout(async () => {
            setLoadingExternal(true);
            try {
              const external = await searchExternalSpecies(query.trim());
              setExternalResults(external);
            } catch (err) {
              setError(err.message);
            } finally {
              setLoadingExternal(false);
            }
          }, EXTERNAL_DEBOUNCE_MS - LOCAL_DEBOUNCE_MS);
        }
      } catch (err) {
        setError(err.message);
      }
    }, LOCAL_DEBOUNCE_MS);

    return () => {
      clearTimeout(localDebounceRef.current);
      clearTimeout(externalDebounceRef.current);
    };
  }, [query]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const selectResult = (result) => {
    setIsOpen(false);
    if (result.id !== undefined) {
      onSelectExisting(result);
    } else {
      onSelectCandidate(result);
    }
  };

  const handleKeyDown = (e) => {
    if (!isOpen || results.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlightedIndex((i) => (i + 1) % results.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlightedIndex((i) => (i - 1 + results.length) % results.length);
    } else if (e.key === "Enter" && highlightedIndex >= 0) {
      e.preventDefault();
      selectResult(results[highlightedIndex]);
    } else if (e.key === "Escape") {
      setIsOpen(false);
    }
  };

  return (
    <div className="plant-search" ref={containerRef}>
      <label>
        Search for a plant
        <input
          type="text"
          placeholder="e.g. Golden Pothos, or a scientific name"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query.trim().length >= 2 && setIsOpen(true)}
          onKeyDown={handleKeyDown}
        />
      </label>

      {error && <p className="error">{error}</p>}

      {isOpen && (
        <ul className="search-dropdown">
          {results.map((result, i) => (
            <li key={result.id ?? `${result.data_source}-${result.external_id}-${i}`}>
              <button
                type="button"
                className={i === highlightedIndex ? "highlighted" : ""}
                onMouseEnter={() => setHighlightedIndex(i)}
                onClick={() => selectResult(result)}
              >
                <strong>{result.common_name}</strong>
                {result.scientific_name && <em> — {result.scientific_name}</em>}
                <span className="tag">
                  {result.id !== undefined ? "in your family's collection" : `from ${result.data_source}`}
                </span>
              </button>
            </li>
          ))}

          {loadingExternal && <li className="hint">Searching online...</li>}

          {!loadingExternal && localResults.length === 0 && externalResults !== null && externalResults.length === 0 && (
            <li className="hint">No matches found anywhere.</li>
          )}

          <li>
            <button type="button" onClick={onManual}>
              Enter it manually instead
            </button>
          </li>
        </ul>
      )}
    </div>
  );
}
