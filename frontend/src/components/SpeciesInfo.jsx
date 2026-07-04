function YesNoFlags({ species }) {
  const flags = [
    ["Cones", species.cones],
    ["Flowers", species.flowers],
    ["Fruits", species.fruits],
    ["Leaf", species.leaf],
  ].filter(([, value]) => value !== null && value !== undefined);

  if (flags.length === 0) return null;

  return (
    <div className="species-flags">
      {flags.map(([label, value]) => (
        <span key={label} className={value ? "flag-yes" : "flag-no"}>
          {label}: {value ? "Yes" : "No"}
        </span>
      ))}
    </div>
  );
}

export default function SpeciesInfo({ species }) {
  const hasBasicInfo =
    species.cycle || species.hardiness_min || species.care_level || species.drought_tolerant !== null || species.indoor !== null;
  const isPoisonous = species.poisonous_to_humans || species.poisonous_to_pets;

  return (
    <div className="species-info-rich">
      {species.description && <p className="species-description">{species.description}</p>}
      {species.other_name && (
        <p className="also-known-as">
          <strong>Also known as:</strong> {species.other_name}
        </p>
      )}

      {isPoisonous && (
        <div className="poison-warning">
          ⚠ Poisonous to {[species.poisonous_to_humans && "humans", species.poisonous_to_pets && "pets"]
            .filter(Boolean)
            .join(" and ")}
        </div>
      )}

      {hasBasicInfo && (
        <dl className="species-detail-grid">
          {species.cycle && (
            <>
              <dt>Cycle</dt>
              <dd>{species.cycle}</dd>
            </>
          )}
          {species.hardiness_min && (
            <>
              <dt>Hardiness Zone</dt>
              <dd>
                {species.hardiness_min}
                {species.hardiness_max && species.hardiness_max !== species.hardiness_min
                  ? `–${species.hardiness_max}`
                  : ""}
              </dd>
            </>
          )}
          {species.care_level && (
            <>
              <dt>Care Level</dt>
              <dd>{species.care_level}</dd>
            </>
          )}
          {species.watering_benchmark && (
            <>
              <dt>Watering Benchmark</dt>
              <dd>{species.watering_benchmark}</dd>
            </>
          )}
          {species.drought_tolerant !== null && species.drought_tolerant !== undefined && (
            <>
              <dt>Drought Tolerant</dt>
              <dd>{species.drought_tolerant ? "Yes" : "No"}</dd>
            </>
          )}
          {species.indoor !== null && species.indoor !== undefined && (
            <>
              <dt>Indoor</dt>
              <dd>{species.indoor ? "Yes" : "No"}</dd>
            </>
          )}
        </dl>
      )}

      <YesNoFlags species={species} />
    </div>
  );
}
