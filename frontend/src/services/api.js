const API_URL = "http://127.0.0.1:8000";


export async function searchNews(query, topK = 5) {

    const response = await fetch(
        `${API_URL}/search`,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                query: query,
                top_k: topK
            })
        }
    );


    if (!response.ok) {

        throw new Error(
            `Search failed: ${response.status}`
        );

    }


    return await response.json();
}