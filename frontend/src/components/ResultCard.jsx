import { useState } from "react";

function ResultCard({ result, rank }) {
    const [showCalculation, setShowCalculation] = useState(false);

    if (!result) {
        return null;
    }

    const score =
        typeof result.score === "number"
            ? result.score
            : 0;

    return (
        <article className="result-card">

            <div className="result-top">

                <div className="rank-badge">
                    #{rank}
                </div>

                <div className="result-title-area">
                    <h3>
                        {result.title || "Untitled article"}
                    </h3>

                    <div className="result-source">
                        {result.source || "Unknown source"}
                    </div>
                </div>

                <div className="score-box">
                    <span className="score-label">
                        Similarity
                    </span>

                    <strong>
                        {score.toFixed(4)}
                    </strong>
                </div>

            </div>

            <div className="result-content">
                <p>
                    {result.content || "No content available."}
                </p>
            </div>

            <div className="metadata">
                <span>
                    FAISS ID: {result.faiss_id ?? "N/A"}
                </span>
            </div>

            <div className="calculation-section">

                <button
                    type="button"
                    className="calculation-toggle"
                    onClick={() =>
                        setShowCalculation(!showCalculation)
                    }
                >
                    <span>
                        How was this result arrived?
                    </span>

                    <span className="toggle-icon">
                        {showCalculation ? "−" : "+"}
                    </span>
                </button>

                {showCalculation && (
                    <div className="calculation-panel">

                        {/* STEP 1 */}
                        <div className="calculation-step">

                            <div className="calculation-number">
                                1
                            </div>

                            <div>
                                <h4>
                                    Query converted to embedding
                                </h4>

                                <p>
                                    The search query is converted
                                    into a numerical embedding vector
                                    using the same embedding model
                                    used for the news articles.
                                </p>

                                <div className="calculation-value">
                                    Embedding dimension: 768
                                </div>
                            </div>

                        </div>

                        {/* STEP 2 */}
                        <div className="calculation-step">

                            <div className="calculation-number">
                                2
                            </div>

                            <div>
                                <h4>
                                    Compare with this article
                                </h4>

                                <p>
                                    The query embedding is compared
                                    with this article's embedding
                                    using vector similarity.
                                </p>

                                <div className="formula">
                                    Similarity = q · d
                                </div>

                                <div className="formula-note">
                                    Because the embeddings are normalized,
                                    the inner product is equivalent to
                                    cosine similarity.
                                </div>
                            </div>

                        </div>

                        {/* STEP 3 */}
                        <div className="calculation-step">

                            <div className="calculation-number">
                                3
                            </div>

                            <div>
                                <h4>
                                    Calculated similarity
                                </h4>

                                <div className="score-calculation">

                                    <span>
                                        Similarity score
                                    </span>

                                    <strong>
                                        {score.toFixed(4)}
                                    </strong>

                                </div>

                                <p>
                                    A higher score means the article's
                                    embedding is more similar to the
                                    search query.
                                </p>
                            </div>

                        </div>

                        {/* STEP 4 */}
                        <div className="calculation-step">

                            <div className="calculation-number">
                                4
                            </div>

                            <div>
                                <h4>
                                    Ranking
                                </h4>

                                <p>
                                    FAISS sorts the retrieved vectors
                                    by similarity score in descending
                                    order.
                                </p>

                                <div className="rank-result">
                                    Result rank:{" "}
                                    <strong>#{rank}</strong>
                                </div>
                            </div>

                        </div>

                    </div>
                )}

            </div>

            <div className="result-footer">

                {result.url && (
                    <a
                        href={result.url}
                        target="_blank"
                        rel="noreferrer"
                        className="read-link"
                    >
                        Read original →
                    </a>
                )}

            </div>

        </article>
    );
}

export default ResultCard;