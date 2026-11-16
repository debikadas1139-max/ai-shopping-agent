const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

export function formatPrice(value) {
  return money.format(Number(value) || 0);
}

// SQLite stores UTC times like "2026-11-14 09:30:00"; show them in the visitor's local time.
export function formatDate(sqliteTimestamp) {
  if (!sqliteTimestamp) return "";
  const date = new Date(String(sqliteTimestamp).replace(" ", "T") + "Z");
  if (Number.isNaN(date.getTime())) return String(sqliteTimestamp);
  return date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export function categoryLabel(category) {
  if (!category) return "Other";
  if (category === "dairy-alt") return "Dairy alternatives";
  return category.charAt(0).toUpperCase() + category.slice(1);
}

export function newId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
  return "id-" + Math.random().toString(16).slice(2) + Date.now().toString(16);
}
