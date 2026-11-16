import { Star } from "lucide-react";

// Shows 1-5 stars plus the number and review count. Works with real data only.
export default function RatingStars({ rating, count, showNumber = true }) {
  if (!count) {
    return <span className="text-sm text-ink/60">No reviews yet</span>;
  }
  const filled = Math.round(rating);
  const label = `Rated ${rating.toFixed(2)} out of 5 from ${count} ${count === 1 ? "review" : "reviews"}`;
  return (
    <span className="inline-flex items-center gap-1.5" role="img" aria-label={label}>
      <span className="inline-flex" aria-hidden="true">
        {[0, 1, 2, 3, 4].map((i) => (
          <Star
            key={i}
            size={15}
            className={i < filled ? "fill-honey text-honey" : "text-mist"}
            strokeWidth={i < filled ? 1.5 : 2}
          />
        ))}
      </span>
      {showNumber && (
        <span className="text-sm font-semibold" aria-hidden="true">
          {rating.toFixed(2)}
        </span>
      )}
      <span className="text-sm text-ink/60" aria-hidden="true">
        ({count})
      </span>
    </span>
  );
}
