import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createPlant } from "../api/plants";
import { getSpecies } from "../api/plantSearch";
import PlantSearchAutocomplete from "../components/PlantSearchAutocomplete";
import SpeciesInfo from "../components/SpeciesInfo";

const emptyManualForm = {
  common_name: "",
  scientific_name: "",
  family: "",
  genus: "",
  watering_frequency: "",
  sunlight: "",
  origin_region: "",
  origin_country: "",
  personal_notes: "",
  acquired_date: "",
};

export default function PlantNewPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // mode: "search" | "confirm" | "manual"
  const [mode, setMode] = useState("search");
  const [chosenSpecies, setChosenSpecies] = useState(null); // { existing: bool, data }
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [notes, setNotes] = useState({ personal_notes: "", acquired_date: "" });
  const [manualForm, setManualForm] = useState(emptyManualForm);
  const [selectError, setSelectError] = useState(null);

  const mutation = useMutation({
    mutationFn: (payload) => createPlant(payload),
    onSuccess: (plant) => {
      queryClient.invalidateQueries({ queryKey: ["plants"] });
      navigate(`/plants/${plant.id}`);
    },
  });

  const selectExisting = async (species) => {
    setSelectError(null);
    setLoadingDetails(true);
    try {
      // Triggers the one-time Perenual details backfill server-side, if this
      // species hasn't been fully looked up by any family member yet.
      const fullSpecies = await getSpecies(species.id);
      setChosenSpecies({ existing: true, data: fullSpecies });
      setMode("confirm");
    } catch (err) {
      setSelectError(err.message);
    } finally {
      setLoadingDetails(false);
    }
  };

  const selectCandidate = (candidate) => {
    setChosenSpecies({ existing: false, data: candidate });
    setMode("confirm");
  };

  const submitConfirm = (e) => {
    e.preventDefault();
    const payload = chosenSpecies.existing
      ? { species_id: chosenSpecies.data.id }
      : { new_species: chosenSpecies.data };
    mutation.mutate({
      ...payload,
      personal_notes: notes.personal_notes || null,
      acquired_date: notes.acquired_date || null,
    });
  };

  const submitManual = (e) => {
    e.preventDefault();
    const { personal_notes, acquired_date, ...speciesFields } = manualForm;
    mutation.mutate({
      new_species: { ...speciesFields, data_source: "manual" },
      personal_notes: personal_notes || null,
      acquired_date: acquired_date || null,
    });
  };

  const updateManual = (field) => (e) => setManualForm({ ...manualForm, [field]: e.target.value });

  return (
    <div className="plant-new-page">
      <h1>Add a plant</h1>

      {mode === "search" && (
        <>
          <PlantSearchAutocomplete
            onSelectExisting={selectExisting}
            onSelectCandidate={selectCandidate}
            onManual={() => setMode("manual")}
          />
          {loadingDetails && <p className="hint">Loading plant details...</p>}
          {selectError && <p className="error">{selectError}</p>}
        </>
      )}

      {mode === "confirm" && chosenSpecies && (
        <form onSubmit={submitConfirm}>
          <div className="species-preview">
            <h2>{chosenSpecies.data.common_name}</h2>
            {chosenSpecies.data.scientific_name && <p className="scientific-name">{chosenSpecies.data.scientific_name}</p>}
            <dl>
              {chosenSpecies.data.family && (
                <>
                  <dt>Family</dt>
                  <dd>{chosenSpecies.data.family}</dd>
                </>
              )}
              {chosenSpecies.data.watering_frequency && (
                <>
                  <dt>Water</dt>
                  <dd>{chosenSpecies.data.watering_frequency}</dd>
                </>
              )}
              {chosenSpecies.data.sunlight && (
                <>
                  <dt>Light</dt>
                  <dd>{chosenSpecies.data.sunlight}</dd>
                </>
              )}
              {chosenSpecies.data.origin_country && (
                <>
                  <dt>Origin</dt>
                  <dd>{chosenSpecies.data.origin_country}</dd>
                </>
              )}
            </dl>
            <SpeciesInfo species={chosenSpecies.data} />
          </div>
          <label>
            Acquired on
            <input
              type="date"
              value={notes.acquired_date}
              onChange={(e) => setNotes({ ...notes, acquired_date: e.target.value })}
            />
          </label>
          <label>
            Personal notes
            <textarea
              rows={4}
              value={notes.personal_notes}
              onChange={(e) => setNotes({ ...notes, personal_notes: e.target.value })}
            />
          </label>
          {mutation.isError && <p className="error">{mutation.error.message}</p>}
          <div className="actions">
            <button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Adding..." : "Add plant"}
            </button>
            <button type="button" onClick={() => setMode("search")}>
              Back
            </button>
          </div>
        </form>
      )}

      {mode === "manual" && (
        <form onSubmit={submitManual}>
          <p className="hint">Manual entry — nothing found in Perenual, Trefle, or GBIF for this plant.</p>
          <label>
            Common name*
            <input type="text" value={manualForm.common_name} onChange={updateManual("common_name")} required />
          </label>
          <label>
            Scientific name
            <input type="text" value={manualForm.scientific_name} onChange={updateManual("scientific_name")} />
          </label>
          <label>
            Family
            <input type="text" value={manualForm.family} onChange={updateManual("family")} />
          </label>
          <label>
            Genus
            <input type="text" value={manualForm.genus} onChange={updateManual("genus")} />
          </label>
          <label>
            Watering needs
            <input type="text" placeholder="e.g. Weekly" value={manualForm.watering_frequency} onChange={updateManual("watering_frequency")} />
          </label>
          <label>
            Light needs
            <input type="text" placeholder="e.g. Indirect light" value={manualForm.sunlight} onChange={updateManual("sunlight")} />
          </label>
          <label>
            Origin region
            <input type="text" value={manualForm.origin_region} onChange={updateManual("origin_region")} />
          </label>
          <label>
            Origin country
            <input type="text" value={manualForm.origin_country} onChange={updateManual("origin_country")} />
          </label>
          <label>
            Acquired on
            <input type="date" value={manualForm.acquired_date} onChange={updateManual("acquired_date")} />
          </label>
          <label>
            Personal notes
            <textarea rows={4} value={manualForm.personal_notes} onChange={updateManual("personal_notes")} />
          </label>
          {mutation.isError && <p className="error">{mutation.error.message}</p>}
          <div className="actions">
            <button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Adding..." : "Add plant"}
            </button>
            <button type="button" onClick={() => setMode("search")}>
              Back to search
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
