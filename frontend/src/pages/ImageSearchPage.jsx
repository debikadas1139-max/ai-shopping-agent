import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Camera, MessageCircle, Upload } from "lucide-react";
import Notice from "../components/Notice";
import ProductCard from "../components/ProductCard";
import Spinner from "../components/Spinner";
import { imageSearch } from "../services/api";

const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_BYTES = 3 * 1024 * 1024; // keep in sync with backend max_image_bytes

function organicLabel(value) {
  if (value === true) return "Label says organic";
  if (value === false) return "Not labelled organic";
  return "Organic status unclear";
}

export default function ImageSearchPage() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [validationError, setValidationError] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const inputRef = useRef(null);
  const navigate = useNavigate();

  // Free the preview URL when it changes or the page closes.
  useEffect(() => () => previewUrl && URL.revokeObjectURL(previewUrl), [previewUrl]);

  function chooseFile(selected) {
    setResult(null);
    setError("");
    if (!selected) return;
    if (!ALLOWED_TYPES.includes(selected.type)) {
      setValidationError("Please choose a JPG, JPEG, PNG or WebP image.");
      return;
    }
    if (selected.size > MAX_BYTES) {
      setValidationError("This image is larger than 3 MB. Please choose a smaller one.");
      return;
    }
    setValidationError("");
    setFile(selected);
    setPreviewUrl(URL.createObjectURL(selected));
  }

  async function submit() {
    if (!file) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      setResult(await imageSearch(file));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function onDrop(event) {
    event.preventDefault();
    chooseFile(event.dataTransfer.files && event.dataTransfer.files[0]);
  }

  return (
    <div>
      <h1 className="text-3xl font-bold">Search by photo</h1>
      <p className="mt-1 max-w-2xl text-ink/70">
        Upload a photo of a product. An AI model reads it and suggests a product type and keywords, then we search the
        catalog with those words. The matches are approximate.
      </p>

      <div className="mt-6 grid gap-6 md:grid-cols-[20rem_1fr]">
        <div>
          <div
            className="card flex min-h-[14rem] flex-col items-center justify-center gap-3 border-dashed p-4 text-center"
            onDragOver={(e) => e.preventDefault()}
            onDrop={onDrop}
          >
            {previewUrl ? (
              <img src={previewUrl} alt="Preview of the selected product" className="max-h-56 rounded-lg object-contain" />
            ) : (
              <>
                <Camera size={36} className="text-leaf" aria-hidden="true" />
                <p className="text-sm text-ink/70">Drop an image here, or choose a file.</p>
              </>
            )}
            <input
              ref={inputRef}
              id="image-input"
              type="file"
              accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
              className="sr-only"
              onChange={(e) => chooseFile(e.target.files && e.target.files[0])}
            />
            <label htmlFor="image-input" className="btn-secondary cursor-pointer">
              <Upload size={16} aria-hidden="true" /> {file ? "Choose a different image" : "Choose image"}
            </label>
            <p className="text-xs text-ink/60">JPG, PNG or WebP, up to 3 MB.</p>
          </div>

          {validationError && (
            <div className="mt-3">
              <Notice type="error">{validationError}</Notice>
            </div>
          )}

          <button type="button" className="btn-primary mt-4 w-full" onClick={submit} disabled={!file || loading}>
            {loading ? "Analyzing…" : "Find matching products"}
          </button>
        </div>

        <div>
          {loading && <Spinner label="Analyzing the photo and searching the catalog…" />}

          {error && (
            <Notice
              type="error"
              title="Image search failed"
              action={file && <button type="button" className="btn-secondary" onClick={submit}>Try again</button>}
            >
              {error}
            </Notice>
          )}

          {result && (
            <div className="space-y-5">
              <div className="card p-4">
                <h2 className="text-lg font-bold">What the AI sees</h2>
                <p className="mt-1 text-sm text-ink/80">{result.analysis.description || "No description returned."}</p>
                <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
                  <div>
                    <dt className="font-semibold">Likely product</dt>
                    <dd>{result.analysis.product_type}</dd>
                  </div>
                  <div>
                    <dt className="font-semibold">Organic</dt>
                    <dd>{organicLabel(result.analysis.is_organic)}</dd>
                  </div>
                  <div className="sm:col-span-2">
                    <dt className="font-semibold">Search keywords</dt>
                    <dd className="mt-1 flex flex-wrap gap-1.5">
                      {result.analysis.search_keywords.length === 0 && <span className="text-ink/60">None</span>}
                      {result.analysis.search_keywords.map((k) => (
                        <span key={k} className="rounded-full bg-leaf-soft px-2.5 py-0.5 text-leaf-deep">{k}</span>
                      ))}
                    </dd>
                  </div>
                  {result.analysis.visual_characteristics.length > 0 && (
                    <div className="sm:col-span-2">
                      <dt className="font-semibold">Visible details</dt>
                      <dd>{result.analysis.visual_characteristics.join(", ")}</dd>
                    </div>
                  )}
                </dl>
              </div>

              <Notice type="info">{result.note}</Notice>

              {result.matches.length > 0 && (
                <>
                  <h2 className="text-xl font-bold">Possible matches ({result.matches.length})</h2>
                  <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                    {result.matches.map((p) => (
                      <ProductCard key={p.id} product={p} />
                    ))}
                  </div>
                </>
              )}

              <button type="button" className="btn-secondary" onClick={() => navigate("/", { state: { imageId: result.image_id } })}>
                <MessageCircle size={16} aria-hidden="true" /> Ask the assistant about this image
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
