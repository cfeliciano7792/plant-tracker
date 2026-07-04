import { Link } from "react-router-dom";

export default function PlantCard({ plant }) {
  const { species } = plant;
  return (
    <Link to={`/plants/${plant.id}`} className="plant-card">
      <h3>{species.common_name}</h3>
      {species.scientific_name && <p className="scientific-name">{species.scientific_name}</p>}
      <dl>
        {species.watering_frequency && (
          <>
            <dt>Water</dt>
            <dd>{species.watering_frequency}</dd>
          </>
        )}
        {species.sunlight && (
          <>
            <dt>Light</dt>
            <dd>{species.sunlight}</dd>
          </>
        )}
      </dl>
    </Link>
  );
}
