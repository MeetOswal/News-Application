import React, { useState } from "react";
import {useNavigate } from "react-router-dom";
import axios from "axios";
import API from "../assets/api"
import "../css/LoginPage.css";
function LoginPage() {
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [error, setError] = useState("")
    const [loggedIn, setLoggedIn] = useState(false)
    const [loading, setLoading] = useState(false)
    const nav = useNavigate()

    const handleSubmit = async(e) => {
        e.preventDefault()
        setError("")
        setLoading(true)
        const formData = new FormData()
        formData.append("email", email)
        formData.append("password", password)

        try {
            await axios.post(`${API}/login`, formData, {
                headers: {
                "Content-Type": "multipart/form-data",
                },
                withCredentials: true, 
            });
            setLoggedIn(true)
            sessionStorage.clear();
        } catch (error) {
            console.log(error);
            (error.response) ? setError(error.response.data.error) : setError("error")
        }finally{
            setLoading(false)
        }
    }

    return (
        <div className="login-container">
            {
                !loggedIn ? (
                    <form onSubmit={handleSubmit} className="login-form">
                        <label htmlFor="email">Email</label>
                        <input type="text" 
                        value = {email}
                        onChange={(e) => setEmail(e.target.value)}
                        required/>
                        <br />
                        <label htmlFor="password">Password</label>
                        <input type="password" 
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required/>
                        <br />
                        <div className="button-container">
                            {loading ? (
                                <button type="Submit" disabled = {true} className="primary-button loading">Submitting...</button>
                            ):(
                                <button type="Submit" disabled = {false} className="primary-button">Sumbit</button>
                            )}
                            
                            <br />
                            <button className="secondary-button" onClick={(e) => nav("/register")}>Register</button>
                        </div>
                    </form>
                ) : (
                    <div className="success-message">
                        <span>Login Succesfull</span>
                        <button className="primary-button" onClick={() => nav("/", {state : true})}>Home</button>
                    </div>
                )
            }
            {
                error && (
                    <div className="error-message">{error}</div>
                )
            }
        </div>
    )
}

export default LoginPage