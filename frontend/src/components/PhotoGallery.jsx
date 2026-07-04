import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { deletePhoto, listPhotos, photoUrl } from "../api/photos";

export default function PhotoGallery({ plantId }) {
  const queryClient = useQueryClient();

  const { data: photos = [], isLoading } = useQuery({
    queryKey: ["plants", plantId, "photos"],
    queryFn: () => listPhotos(plantId),
  });

  const deleteMutation = useMutation({
    mutationFn: (photoId) => deletePhoto(plantId, photoId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["plants", plantId, "photos"] }),
  });

  if (isLoading) return null;
  if (photos.length === 0) return <p className="hint">No photos yet.</p>;

  return (
    <div className="photo-gallery">
      {photos.map((photo) => (
        <div key={photo.id} className="photo-thumb">
          <img src={photoUrl(plantId, photo.id)} alt="" />
          <button type="button" className="danger" onClick={() => deleteMutation.mutate(photo.id)}>
            Remove
          </button>
        </div>
      ))}
    </div>
  );
}
