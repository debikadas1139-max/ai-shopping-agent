// Every call to the FastAPI backend lives in this file.
// Endpoint paths and field names match backend/app/api/*.py and backend/app/schemas.py.

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(message, status = 0, code = "") {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

function messageFromBody(data, status) {
  if (data && typeof data.detail === "string") return data.detail;
  if (data && Array.isArray(data.detail)) {
    // FastAPI validation errors: [{loc: [...], msg: "..."}]
    return data.detail.map((d) => d.msg).join(". ");
  }
  return `The request failed (status ${status}).`;
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, options);
  } catch (err) {
    if (err && err.name === "AbortError") throw err;
    throw new ApiError(`Cannot reach the server at ${BASE_URL}. Is the backend running?`, 0, "network_error");
  }
  let data = null;
  const text = await response.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }
  if (!response.ok) {
    throw new ApiError(messageFromBody(data, response.status), response.status, data && data.code ? data.code : "");
  }
  return data;
}

function postJson(path, body) {
  return request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

function toQuery(params) {
  const query = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== "" && value !== null && value !== undefined) query.set(key, String(value));
  });
  const text = query.toString();
  return text ? `?${text}` : "";
}

export const getHealth = () => request("/api/health");

// filters: { q, category, min_price, max_price, min_rating, is_organic, sort, limit, offset }
export const getProducts = (filters) => request(`/api/products${toQuery(filters)}`);
export const getCategories = () => request("/api/products/categories");
export const getProduct = (id) => request(`/api/products/${id}`);
export const getReviews = (id) => request(`/api/products/${id}/reviews`);

export const compareProducts = (productIds) => postJson("/api/compare", { product_ids: productIds });

// items: [{ product_id, quantity }]. Prices are never sent; the server looks them up.
export const validateCart = (items) => postJson("/api/cart/validate", { items });

// messages: [{ role, content, shown_products? }]
export const sendChat = (messages, imageId) =>
  postJson("/api/chat", { messages, ...(imageId ? { image_id: imageId } : {}) });

export function imageSearch(file) {
  const form = new FormData();
  form.append("file", file); // the browser sets the multipart Content-Type header itself
  return request("/api/image-search", { method: "POST", body: form });
}

// payload: { items, confirmed, confirmed_total, idempotency_key }
export const createOrder = (payload) => postJson("/api/orders", payload);
export const getOrders = () => request("/api/orders");
export const getOrder = (id) => request(`/api/orders/${id}`);
