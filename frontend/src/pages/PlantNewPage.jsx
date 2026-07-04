import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createPlant } from "../api/plants";

const emptyForm = {
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
  const [form, setForm] = useState(emptyForm);

  const mutation = useMutation({
    mutationFn: (payload) => createPlant(payload),
    onSuccess: (plant) => {
      queryClient.invalidateQueries({ queryKey: ["plants"] });
      navigate(`/plants/${plant.id}`);
    },
  });

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const handleSubmit = (e) => {
    e.preventDefault();
    const { personal_notes, acquired_date, ...speciesFields } = form;
    mutation.mutate({
      new_species: { ...speciesFields, data_source: "manual" },
      personal_notes: personal_notes || null,
      acquired_date: acquired_date || null,
    });
  };

  return (
    <div className="plant-new-page">
      <h1>Add a plant</h1>
      <p className="hint">
        Manual entry for now — searching a plant database to autofill this form is coming soon.
      </p>
      <form onSubmit={handleSubmit}>
        <label>
          Common name*
          <input type="text" value={form.common_name} onChange={update("common_name")} required />
        </label>
        <label>
          Scientific name
          <input type="text" value={form.scientific_name} onChange={update("scientific_name")} />
        </label>
        <label>
          Family
          <input type="text" value={form.family} onChange={update("family")} />
        </label>
        <label>
          Genus
          <input type="text" value={form.genus} onChange={update("genus")} />
        </label>
        <label>
          Watering needs
          <input
            type="text"
            placeholder="e.g. Weekly"
            value={form.watering_frequency}
            onChange={update("watering_frequency")}
          />
        </label>
        <label>
          Light needs
          <input
            type="text"
            placeholder="e.g. Indirect light"
            value={form.sunlight}
            onChange={update("sunlight")}
          />
        </label>
        <label>
          Origin region
          <input type="text" value={form.origin_region} onChange={update("origin_region")} />
        </label>
        <label>
          Origin country
          <input type="text" value={form.origin_country} onChange={update("origin_country")} />
        </label>
        <label>
          Acquired on
          <input type="date" value={form.acquired_date} onChange={update("acquired_date")} />
        </label>
        <label>
          Personal notes
          <textarea value={form.personal_notes} onChange={update("personal_notes")} rows={4} />
        </label>
        {mutation.isError && <p className="error">{mutation.error.message}</p>}
        <button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Adding..." : "Add plant"}
        </button>
      </form>
    </div>
  );
}
