import { useState, useEffect } from "react";
import "./App.css";

const API = "http://localhost:8000";

function App() {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch the review history from the backend when the page loads.
  useEffect(() => {
    fetch(`${API}/reviews`)
      .then((res) => {
        if (!res.ok) throw new Error(`Server responded ${res.status}`);
        return res.json();
      })
      .then((data) => setReviews(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const clean = reviews.filter((r) => r.verdict === "clean").length;

  return (
    <div className="app">
      <header className="header">
        <h1>ReviewPilot</h1>
        <p className="subtitle">Automated PR review history</p>
      </header>

      {!loading && !error && reviews.length > 0 && (
        <div className="stats">
          <div className="stat"><b>{reviews.length}</b><span>total reviews</span></div>
          <div className="stat"><b>{clean}</b><span>clean</span></div>
          <div className="stat"><b>{reviews.length - clean}</b><span>with issues</span></div>
        </div>
      )}

      {loading && <p className="muted">Loading reviews…</p>}
      {error && <p className="error">Couldn’t load reviews: {error}</p>}
      {!loading && !error && reviews.length === 0 && (
        <p className="muted">No reviews yet. Open a pull request to see one appear here.</p>
      )}

      <div className="list">
        {reviews.map((r) => (
          <article key={r.id} className="card">
            <div className="card-top">
              <span className="repo">
                {r.repo} <span className="pr">#{r.pr_number}</span>
              </span>
              <span className={`badge ${r.verdict === "clean" ? "ok" : "warn"}`}>
                {r.verdict}
              </span>
            </div>
            <p className="review">{r.review}</p>
            <div className="meta">
              <span>{new Date(r.created_at).toLocaleString()}</span>
              {r.duration_ms != null && (
                <span>{(r.duration_ms / 1000).toFixed(1)}s</span>
              )}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

export default App;