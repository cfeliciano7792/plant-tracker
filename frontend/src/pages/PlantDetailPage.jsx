import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { deletePlant, getPlant, updatePlant } from "../api/plants";
import PhotoGallery from "../components/PhotoGallery";
import PhotoUploader from "../components/PhotoUploader";

export default function PlantDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [editingNotes, setEditingNotes] = useState(false);
  const [notesDraft, setNotesDraft] = useState("");

  const { data: plant, isLoading, error } = useQuery({
    queryKey: ["plants", id],
    queryFn: () => getPlant(id),
  });

  const updateMutation = useMutation({
    mutationFn: (data) => updatePlant(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plants", id] });
      queryClient.invalidateQueries({ queryKey: ["plants"] });
      setEditingNotes(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deletePlant(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plants"] });
      navigate("/plants");
    },
  });

  if (isLoading) return <p>Loading...</p>;
  if (error) return <p className="error">Failed to load plant: {error.message}</p>;

  const { species } = plant;

  const startEditing = () => {
    setNotesDraft(plant.personal_notes || "");
    setEditingNotes(true);
  };

  return (
    <div className="plant-detail-page">
      <h1>{species.common_name}</h1>
      {species.scientific_name && <p className="scientific-name">{species.scientific_name}</p>}

      <dl className="species-info">
        {species.family && (
          <>
            <dt>Family</dt>
            <dd>{species.family}</dd>
          </>
        )}
        {species.genus && (
          <>
            <dt>Genus</dt>
            <dd>{species.genus}</dd>
          </>
        )}
        {species.watering_frequency && (
          <>
            <dt>Watering</dt>
            <dd>{species.watering_frequency}</dd>
          </>
        )}
        {species.sunlight && (
          <>
            <dt>Light</dt>
            <dd>{species.sunlight}</dd>
          </>
        )}
        {(species.origin_region || species.origin_country) && (
          <>
            <dt>Origin</dt>
            <dd>{[species.origin_country, species.origin_region].filter(Boolean).join(", ")}</dd>
          </>
        )}
        {plant.acquired_date && (
          <>
            <dt>Acquired</dt>
            <dd>{plant.acquired_date}</dd>
          </>
        )}
      </dl>

      <section className="personal-notes">
        <h2>Personal notes</h2>
        {editingNotes ? (
          <>
            <textarea
              value={notesDraft}
              onChange={(e) => setNotesDraft(e.target.value)}
              rows={4}
            />
            <div className="actions">
              <button onClick={() => updateMutation.mutate({ personal_notes: notesDraft })}>
                Save
              </button>
              <button onClick={() => setEditingNotes(false)}>Cancel</button>
            </div>
          </>
        ) : (
          <>
            <p>{plant.personal_notes || "No notes yet."}</p>
            <button onClick={startEditing}>Edit notes</button>
          </>
        )}
      </section>

      <section className="photos">
        <h2>Photos</h2>
        <PhotoGallery plantId={id} />
        <PhotoUploader plantId={id} />
      </section>

      <button
        className="danger"
        onClick={() => {
          if (confirm(`Remove ${species.common_name} from your collection?`)) {
            deleteMutation.mutate();
          }
        }}
      >
        Delete plant
      </button>
    </div>
  );
}
