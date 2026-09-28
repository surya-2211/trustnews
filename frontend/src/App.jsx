import { useState } from "react";

import { searchNews } from "./services/api";

import SearchBar from "./components/SearchBar";
import SearchResults from "./components/SearchResults";
import RetrievalProcess from "./components/RetrievalProcess";
import ArticleGenerator from "./components/ArticleGenerator";

function App() {

    const [results, setResults] = useState([]);
    const [steps, setSteps] = useState([]);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const [searchedQuery, setSearchedQuery] = useState("");


    async function handleSearch(query) {

        if (!query.trim()) {
            return;
        }


        setLoading(true);
        setError("");
        setSearchedQuery(query);


        try {

            const data = await searchNews(
                query,
                5
            );


            setResults(
                data.results || []
            );


            setSteps(
                data.retrieval_steps || []
            );


        } catch (err) {

            console.error(err);

            setResults([]);
            setSteps([]);

            setError(
                "Unable to retrieve news. Please make sure the API is running."
            );

        } finally {

            setLoading(false);

        }

    }


    return (

        <div className="app">

            <header className="hero">

                <div className="brand">

                    <div className="brand-mark">
                        TN
                    </div>

                    <span>
                        TrustNews
                    </span>

                </div>


                <div className="hero-content">

                    <span className="hero-eyebrow">
                        SEMANTIC NEWS SEARCH
                    </span>

                    <h1>
                        Search news by meaning,
                        <br />
                        not just keywords.
                    </h1>

                    <p>
                        TrustNews uses embeddings and FAISS
                        similarity search to find the most
                        relevant news articles.
                    </p>

                </div>


                <SearchBar
                    onSearch={handleSearch}
                    loading={loading}
                />

            </header>


            <main className="main-content">

                {error && (

                    <div className="error">
                        {error}
                    </div>

                )}


                {searchedQuery && !loading && !error && (

                    <div className="search-info">

                        <span>
                            Results for
                        </span>

                        <strong>
                            "{searchedQuery}"
                        </strong>

                    </div>

                )}


                <RetrievalProcess
                    steps={steps}
                />


                <SearchResults
                    results={results}
                />

                {!loading && results.length > 0 && searchedQuery && (
                <ArticleGenerator
                    query={searchedQuery}
                    results={results}
                />
            )}


                {!loading &&
                    searchedQuery &&
                    !results.length &&
                    !error && (

                        <div className="empty-state">

                            <h2>
                                No results found
                            </h2>

                            <p>
                                Try searching with a different
                                phrase or topic.
                            </p>

                        </div>

                    )}

            </main>

        </div>

    );
}


export default App;