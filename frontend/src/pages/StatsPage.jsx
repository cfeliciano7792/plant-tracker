import { useQuery } from "@tanstack/react-query";
import { getStats } from "../api/stats";

function GroupList({ title, groups }) {
  if (!groups || groups.length === 0) return null;
  return (
    <div className="stats-group">
      <h2>{title}</h2>
      <ul>
        {groups.map((g) => (
          <li key={g.label}>
            <span>{g.label}</span>
            <span className="count">{g.count}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function StatsPage() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ["stats"],
    queryFn: getStats,
  });

  if (isLoading) return <p>Loading stats...</p>;
  if (error) return <p className="error">Failed to load stats: {error.message}</p>;

  if (stats.total_count === 0) {
    return (
      <div className="stats-page">
        <h1>Collection Stats</h1>
        <p>Add some plants to see stats about your collection.</p>
      </div>
    );
  }

  return (
    <div className="stats-page">
      <h1>Collection Stats</h1>
      <p className="total-count">{stats.total_count} plants in your collection</p>
      <div className="stats-groups">
        <GroupList title="By native region" groups={stats.by_origin_region} />
        <GroupList title="By native country" groups={stats.by_origin_country} />
        <GroupList title="By family" groups={stats.by_family} />
        <GroupList title="By genus" groups={stats.by_genus} />
      </div>
    </div>
  );
}
