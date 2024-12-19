import React, { useEffect } from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import API from "../assets/api";
import "../css/CreateUser.css";

function CreateUser() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [userCreated, setUserCreated] = useState(false);
  const [keywords, setKeywords] = useState([]);
  const [showKeywords, setShowKeywords] = useState(false);
  const [selectedKeywords, setSelectedKeywords] = useState([]);
  const [otherInput, setotherInput] = useState("");
  const [searchResponse, setSearchResponse] = useState([]);
  const nav = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    const formData = new FormData();
    formData.append("email", email);
    formData.append("name", name);
    formData.append("password", password);
    formData.append("preferences", selectedKeywords);
    try {
      await axios.post(`${API}/register`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        withCredentials: true,
      });
      setUserCreated(true);
    } catch (error) {
      console.log(error);
      error.response ? setError(error.response.data.error) : setError("error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const getKeywords = async () => {
      try {
        const response = await axios.get(`${API}/popular-keywords`, {
          withCredentials: true,
        });
        console.log(response.data.message);
        setKeywords(response.data.message);
      } catch (error) {
        error.response
          ? setError(error.response.data.error)
          : console.log(error);
      }
    };
    getKeywords();
  }, []);

  const handleselectedKeywords = (key, index) => {
    setSelectedKeywords((currentState) =>
      currentState.includes(key)
        ? currentState.filter((value) => value != key)
        : [...currentState, key]
    );
    index > 9 && setKeywords((state) => state.filter((value) => value != key));
  };

  const handleFindKeyword = async () => {
    try {
      const response = await axios.get(
        `${API}/search-keyword?query=${otherInput}`,
        {
          withCredentials: true,
        }
      );
      setSearchResponse(response.data.message);
    } catch (error) {
      console.log(error);
    }
  };
  return (
    <div className="create-user-container">
      {!userCreated ? (
        <form onSubmit={handleSubmit} className="user-form">
          {!showKeywords ? (
            <div className="user-details">
              <label htmlFor="name">Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
              <br />
              <label htmlFor="email">Email</label>
              <input
                type="text"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <br />
              <label htmlFor="password">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <br />
              <button
                className="primary-button"
                onClick={() => setShowKeywords(true)}
                disabled={showKeywords}
              >
                {loading ? "Loading..." : "Next"}
              </button>
            </div>
          ) : (
            <div className="keywords-section">
              <h4>Select Your Favorite Keywords</h4>
              <div className="keywords-list">
                {keywords.map((key, index) => {
                  return (
                    <div key={key} className="keyword-item">
                      <input
                        type="checkbox"
                        checked={selectedKeywords.includes(key)}
                        onChange={(e) => handleselectedKeywords(key, index)}
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
                  value={otherInput}
                  onChange={(e) => setotherInput(e.target.value)}
                />
                <button type="button" className="secondary-button" onClick={(e) => handleFindKeyword()}>
                  Find Keyword
                </button>

                <div className="search-results">
                  {searchResponse &&
                    searchResponse.map((key) => {
                      return (
                        <div key={key} className="keyword-item">
                          <input
                            type="checkbox"
                            checked={selectedKeywords.includes(key)}
                            onChange={(e) => {
                              handleselectedKeywords(key);
                              setKeywords((currentState) => [
                                ...currentState,
                                key,
                              ]);
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
              <button type="Submit" disabled={selectedKeywords.length < 3}>
                Submit
              </button>
            </div>
          )}
        </form>
      ) : (
        <div className="user-created">
          <h5>User Created</h5>
          <button className="primary-button" onClick={(e) => nav("/login-page")}>Login</button>
        </div>
      )}
      {error && <div className="error-message">{error}</div>}
    </div>
  );
}

export default CreateUser;
