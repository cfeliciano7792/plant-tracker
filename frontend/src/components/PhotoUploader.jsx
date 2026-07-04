import { useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { uploadPhoto } from "../api/photos";

export default function PhotoUploader({ plantId }) {
  const queryClient = useQueryClient();
  const inputRef = useRef(null);
  const [error, setError] = useState(null);

  const mutation = useMutation({
    mutationFn: (file) => uploadPhoto(plantId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plants", plantId, "photos"] });
      if (inputRef.current) inputRef.current.value = "";
    },
    onError: (err) => setError(err.message),
  });

  const handleChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setError(null);
    mutation.mutate(file);
  };

  return (
    <div className="photo-uploader">
      <label>
        Add a photo
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp,image/gif"
          onChange={handleChange}
          disabled={mutation.isPending}
        />
      </label>
      {mutation.isPending && <p className="hint">Uploading...</p>}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
