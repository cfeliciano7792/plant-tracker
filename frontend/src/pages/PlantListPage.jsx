import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { listPlants } from "../api/plants";
import PlantCard from "../components/PlantCard";
import PlantFilters from "../components/PlantFilters";

export default function PlantListPage() {
  const { data: allPlants = [], isLoading, error } = useQuery({
    queryKey: ["plants"],
    queryFn: () => listPlants(),
  });
  const [filters, setFilters] = useState({});

  const filteredPlants = useMemo(() => {
    return allPlants.filter((plant) => {
      const s = plant.species;
      if (filters.family && s.family !== filters.family) return false;
      if (filters.genus && s.genus !== filters.genus) return false;
      if (filters.watering_frequency && s.watering_frequency !== filters.watering_frequency) return false;
      if (filters.sunlight && s.sunlight !== filters.sunlight) return false;
      return true;
    });
  }, [allPlants, filters]);

  if (isLoading) return <p>Loading your plants...</p>;
  if (error) return <p className="error">Failed to load plants: {error.message}</p>;

  return (
    <div className="plant-list-page">
      <header>
        <h1>My Plants</h1>
        <Link to="/plants/new" className="button">
          + Add a plant
        </Link>
      </header>

      {allPlants.length > 0 && (
        <PlantFilters allPlants={allPlants} filters={filters} onChange={setFilters} />
      )}

      {allPlants.length === 0 ? (
        <p>You haven't added any plants yet.</p>
      ) : filteredPlants.length === 0 ? (
        <p>No plants match those filters.</p>
      ) : (
        <div className="plant-grid">
          {filteredPlants.map((plant) => (
            <PlantCard key={plant.id} plant={plant} />
          ))}
        </div>
      )}
    </div>
  );
}
