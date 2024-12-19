import React, {useState} from "react";
import axios from "axios";
import "../css/Search.css"
import API from "../assets/api";
function Search() {
    const [searchQuery, setSearchQuery] = useState("");
    const [searchResult, setSearchResult] = useState("");
    const [loading, setLoading] = useState(false);
    const handleSearch = async () => {
        try {
          setLoading(true)
          const response = await axios.get(`${API}/search?query=${searchQuery}`, {
            withCredentials : true
          });
          setSearchResult(response.data.response); 
        } catch (error) {
          console.error("Search API Error:", error);
        }finally{
          setLoading(false)
        }
      };

      return (
            <div>
                <div className="search-section">
                <input
                    type="text"
                    className="search-bar"
                    placeholder="Enter your query"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    
                />
                <button onClick={handleSearch} className="search-button" disabled = {loading}>
                    Search
                </button>
                </div>
                {loading && (
                  <h4>Getting Results...</h4>
                )}
        
                {searchResult && (
                    <div className="search-result" id="search-result">
                    <h3 className="result-title"> Search Result:</h3>
                    <p className="result-description">{searchResult}</p>
                    </div>
                )}
            </div>
      )
}

export default Search

