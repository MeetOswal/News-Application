import React, { useEffect } from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import API from "../assets/api";
import "./CreateUser.css"; // Add a CSS file for custom styling

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
    const [otherInput, setOtherInput] = useState("");
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
            error.response ? setError(error.response.data.error) : setError("An error occurred");
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
                setKeywords(response.data.message);
            } catch (error) {
                error.response ? setError(error.response.data.error) : console.log(error);
            }
        };
        getKeywords();
    }, []);

    const handleSelectedKeywords = (key, index) => {
        setSelectedKeywords((currentState) => (
            currentState.includes(key)
                ? currentState.filter((value) => value !== key)
                : [...currentState, key]
        ));
        index > 9 && setKeywords((state) => state.filter((value) => value !== key));
    };

    const handleFindKeyword = async () => {
        try {
            const response = await axios.get(`${API}/search-keyword?query=${otherInput}`, {
                withCredentials: true,
            });
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
                            <h2>Create Your Account</h2>
                            <label htmlFor="name">Name</label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="Enter your name"
                                required
                            />
                            <label htmlFor="email">Email</label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="Enter your email"
                                required
                            />
                            <label htmlFor="password">Password</label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Enter your password"
                                required
                            />
                            <button
                                type="button"
                                className="primary-button"
                                onClick={() => setShowKeywords(true)}
                                disabled={showKeywords}
                            >
                                {loading ? "Loading..." : "Next"}
                            </button>
                        </div>
                    ) : (
                        <div className="keywords-section">
                            <h2>Select Your Favorite Keywords</h2>
                            <div className="keywords-list">
                                {keywords.map((key, index) => (
                                    <div key={key} className="keyword-item">
                                        <input
                                            type="checkbox"
                                            checked={selectedKeywords.includes(key)}
                                            onChange={() => handleSelectedKeywords(key, index)}
                                        />
                                        <label>{key}</label>
                                    </div>
                                ))}
                            </div>
                            <div className="other-keywords">
                                <input
                                    type="text"
                                    placeholder="Search or add custom keyword"
                                    value={otherInput}
                                    onChange={(e) => setOtherInput(e.target.value)}
                                />
                                <button
                                    type="button"
                                    className="secondary-button"
                                    onClick={handleFindKeyword}
                                >
                                    Find Keyword
                                </button>
                                <div className="search-results">
                                    {searchResponse.map((key) => (
                                        <div key={key} className="keyword-item">
                                            <input
                                                type="checkbox"
                                                checked={selectedKeywords.includes(key)}
                                                onChange={() => {
                                                    handleSelectedKeywords(key);
                                                    setSearchResponse((state) => state.filter((value) => value !== key));
                                                    setKeywords((currentState) => [...currentState, key]);
                                                }}
                                            />
                                            <label>{key}</label>
                                        </div>
                                    ))}
                                </div>
                            </div>
                            <button
                                type="submit"
                                className="primary-button"
                                disabled={selectedKeywords.length < 3}
                            >
                                Submit
                            </button>
                        </div>
                    )}
                </form>
            ) : (
                <div className="user-created">
                    <h2>Account Created Successfully!</h2>
                    <button
                        className="primary-button"
                        onClick={() => nav("/login-page")}
                    >
                        Go to Login
                    </button>
                </div>
            )}
            {error && <div className="error-message">{error}</div>}
        </div>
    );
}

export default CreateUser;
