function uniqueValues(plants, path) {
  const values = plants.map((p) => p.species[path]).filter(Boolean);
  return [...new Set(values)].sort();
}

export default function PlantFilters({ allPlants, filters, onChange }) {
  const families = uniqueValues(allPlants, "family");
  const genera = uniqueValues(allPlants, "genus");
  const waterings = uniqueValues(allPlants, "watering_frequency");
  const sunlights = uniqueValues(allPlants, "sunlight");

  const set = (field) => (e) => onChange({ ...filters, [field]: e.target.value });

  return (
    <div className="plant-filters">
      <select value={filters.family || ""} onChange={set("family")}>
        <option value="">All families</option>
        {families.map((f) => (
          <option key={f} value={f}>
            {f}
          </option>
        ))}
      </select>
      <select value={filters.genus || ""} onChange={set("genus")}>
        <option value="">All genera</option>
        {genera.map((g) => (
          <option key={g} value={g}>
            {g}
          </option>
        ))}
      </select>
      <select value={filters.watering_frequency || ""} onChange={set("watering_frequency")}>
        <option value="">Any watering need</option>
        {waterings.map((w) => (
          <option key={w} value={w}>
            {w}
          </option>
        ))}
      </select>
      <select value={filters.sunlight || ""} onChange={set("sunlight")}>
        <option value="">Any light need</option>
        {sunlights.map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>
    </div>
  );
}
