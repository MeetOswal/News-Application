import React, {useState, useEffect} from "react";
import axios from "axios";
import API from "../assets/api";
import "../css/createUser"
function AddKeywords() {
    const [search, setSearch] = useState("");
    const [searchResults, setSearchResult] = useState([]);
    const [selectedKeywords, setSelectedKeywords] = useState([]);
    const [response, setResponse] = useState([])
    const [error, setError] = useState("")
    const [loading, setLoading] = useState(false)
    const handleFindKeyword = async () => {
        try {
          const response = await axios.get(
            `${API}/search-keyword?query=${search}`,
            {
              withCredentials: true,
            }
          );
          setSearchResult(response.data.message);
        } catch (error) {
          console.log(error);
        }
      };

      const handleselectedKeywords = (key) => {
        setSelectedKeywords((currentState) =>
          currentState.includes(key)
            ? currentState.filter((value) => value != key)
            : [...currentState, key]
        );
      };

      const handleSubmit = async(event) => {
        event.preventDefault();
        setError("");
        setLoading(true);
        const formData = new FormData()
        formData.append('preferences', selectedKeywords)
        try {
            const response = await axios.post(`${API}/update-preferences`, formData, {
                headers: {
                  "Content-Type": "multipart/form-data",
                },
                withCredentials: true,
              });
            setResponse(response.data.message)
            setSelectedKeywords([])
        } catch (error) {
            error.response ? setError(error.response.data.error) : console.log(error);
        }finally{
            setLoading(false)
        }

      }
    

    return (
        <div className="keywords-section">
              <h4>Select Your Favorite Keywords</h4>
              <div className="keywords-list">
                {selectedKeywords.map((key, index) => {
                  return (
                    <div key={key} className="keyword-item">
                      <input
                        type="checkbox"
                        checked={selectedKeywords.includes(key)}
                        onChange={(e) => handleselectedKeywords(key)}
                      />
                      <label htmlFor={key}>{key}</label>
                    </div>
                  );
                })}
              </div>

              <div className="other-keywords">
                <input
                  type="text"
                  placeholder="Other"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <button type="button" className="secondary-button" onClick={(e) => handleFindKeyword()}>
                  {!loading ?  "Find Keyword" : "Finding"}
                </button>

                <div className="search-results">
                  {searchResults &&
                    searchResults.map((key) => {
                      return (
                        <div key={key} className="keyword-item">
                          <input
                            type="checkbox"
                            checked={selectedKeywords.includes(key)}
                            onChange={(e) => {
                              handleselectedKeywords(key);
                              return;
                            }}
                            disabled = {selectedKeywords.includes(key)}
                          />
                          <label htmlFor={key}>{key}</label>
                        </div>
                      );
                    })}
                </div>
              </div>

              <br />
              <button onClick={(e) => handleSubmit(e)} disabled={selectedKeywords.length <= 0}>
                {!loading ? "Submit" : "Sending..."}
              </button>
              {error && (
                <h4>{error}</h4>
              )}
              {response && (
                <h4>{response}</h4>
              )}
            </div>
    )
}

export default AddKeywords