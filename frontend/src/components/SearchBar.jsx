import { useState } from "react";

function SearchBar({
    onSearch,
    loading
}) {

    const [query, setQuery] = useState("");


    function handleSubmit(event) {

        event.preventDefault();

        if (!query.trim()) {
            return;
        }

        onSearch(query);

    }


    return (

        <form
            onSubmit={handleSubmit}
            className="search-bar"
        >

            <div className="search-input-wrapper">

                <span className="search-icon">
                    ⌕
                </span>

                <input
                    type="text"
                    placeholder="Search news..."
                    value={query}
                    onChange={(event) =>
                        setQuery(event.target.value)
                    }
                />

            </div>


            <button
                type="submit"
                disabled={loading || !query.trim()}
            >

                {loading
                    ? "Searching..."
                    : "Search"
                }

            </button>

        </form>

    );
}

export default SearchBar;