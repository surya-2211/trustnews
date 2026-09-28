import { useState } from "react";

function ArticleGenerator({ query, results }) {

    const [loading, setLoading] = useState(false);
    const [articleUrl, setArticleUrl] = useState("");
    const [error, setError] = useState("");

    async function generateArticle() {

        if (!query || !query.trim()) {
            setError("Please enter a search query first.");
            return;
        }

        if (!results || results.length === 0) {
            setError(
                "Search for some news articles before generating an article."
            );
            return;
        }

        setLoading(true);
        setError("");
        setArticleUrl("");

        try {

            const response = await fetch(
                "http://127.0.0.1:8000/generate-article",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        query: query,
                        results: results
                    })
                }
            );

            if (!response.ok) {

                const errorData =
                    await response.json().catch(() => null);

                throw new Error(
                    errorData?.detail ||
                    `Article generation failed: ${response.status}`
                );
            }

            const data = await response.json();

            setArticleUrl(
                `http://127.0.0.1:8000${data.html_file}`
            );

        } catch (err) {

            setError(
                err.message ||
                "Unable to generate article."
            );

        } finally {

            setLoading(false);

        }
    }

    return (
        <section className="article-generator">

            <div className="article-generator-content">

                <div className="article-generator-icon">
                    ✦
                </div>

                <div className="article-generator-info">

                    <div className="article-generator-label">
                        TRUSTNEWS AI
                    </div>

                    <h2>
                        Generate a complete article
                    </h2>

                    <p>
                        Transform the retrieved news into a
                        source-grounded article using the
                        available evidence.
                    </p>

                    {query && (
                        <div className="article-query-preview">

                            <span>
                                Based on
                            </span>

                            <strong>
                                "{query}"
                            </strong>

                        </div>
                    )}

                </div>

                <button
                    className="generate-article-button"
                    onClick={generateArticle}
                    disabled={loading}
                >

                    {loading ? (

                        <>
                            <span className="button-spinner"></span>
                            Generating...
                        </>

                    ) : (

                        <>
                            Generate Article
                            <span className="button-arrow">
                                →
                            </span>
                        </>

                    )}

                </button>

            </div>


            {error && (

                <div className="article-generator-error">

                    <span className="error-icon">
                        !
                    </span>

                    <span>
                        {error}
                    </span>

                </div>

            )}


            {articleUrl && (

                <div className="article-generated-success">

                    <div className="success-icon">
                        ✓
                    </div>

                    <div className="success-content">

                        <strong>
                            Article generated successfully
                        </strong>

                        <p>
                            Your evidence-based TrustNews article
                            is ready to read.
                        </p>

                    </div>

                    <a
                        href={articleUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="open-article-button"
                    >
                        Open Article
                        <span>
                            →
                        </span>
                    </a>

                </div>

            )}

        </section>
    );
}

export default ArticleGenerator;