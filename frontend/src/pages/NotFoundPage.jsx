import { Link } from "react-router-dom";
import { Compass } from "lucide-react";
import EmptyState from "../components/EmptyState";

export default function NotFoundPage() {
  return (
    <EmptyState icon={Compass} title="Page not found" action={<Link to="/" className="btn-primary">Go to the assistant</Link>}>
      That page does not exist.
    </EmptyState>
  );
}
