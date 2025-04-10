import React, { useState } from "react";
import axios from "axios";
import API from "../assets/api";

function Logout({logout}) {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState("")

    const handleSubmit = async(e) => {
        // e.preventDefault()
        setError("")
        setLoading(true)

        try {
            await axios.get(`${API}/logout`, {
                withCredentials: true, 
            });
        } catch (error) {
            console.log(error);
            (error.response) ? setError(error.response.data.error) : setError("error")
        }finally{
            setLoading(false)
            logout()
        }
    }

    return (
            <button onClick={handleSubmit} disabled = {loading}>{!loading ? (
                <span>Logout</span>
            ) : (
                <span>Loading</span>
            )}</button>
    )
}

export default Logout