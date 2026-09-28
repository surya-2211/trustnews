import ResultCard from "./ResultCard";

function SearchResults({ results }) {
    if (!results || results.length === 0) {
        return (
            <div className="no-results">
                No results found.
            </div>
        );
    }

    return (
        <section className="results-section">

            <h2>Retrieved Results</h2>

            <div className="results-list">

                {results.map((result, index) => (
                    <ResultCard
                        key={result.faiss_id ?? index}
                        result={result}
                        rank={index + 1}
                    />
                ))}

            </div>

        </section>
    );
}

export default SearchResults;