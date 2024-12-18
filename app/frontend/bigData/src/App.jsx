import { useEffect, useState } from 'react'
import axios from 'axios';
import { Link } from 'react-router-dom';
import Logout from './components/logout';
import API from "./assets/api"
function App() {
  
  const [rec, setRec] = useState(0);
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [prevData, setPrevData] = useState([])
  const [loggedIn, setLoggedIn] = useState(false)
  const [apiCalled, setApiCalled] = useState(false)
  const getData = async() => {
    try {
      
      const response = await axios.get(`${API}/recommendations/?prev_rec=${rec}`, {
        withCredentials: true,
      });
      
      setData((currentState) => ([...currentState, ...response.data.recommendations]))
      setRec(response.data.page)
      setLoggedIn(response.data.loggedIn)
    } catch (error) {
      console.error('Error fetching data:', error);
    }finally{
      if (loading) {
        setLoading(false)
      } 
    }
  }

  useEffect(() => {
    const callGetData = async() => {
      await getData()
    }
    callGetData();
  },[])

  const handleLogout = async() => {
    setLoggedIn(false)
    setRec(0)
    setData([])
    setPrevData([])
    setLoading(true);
    await getData()
    setLoading(false);
  }

  const handleAddMoreRecommendation = async() => {
    setApiCalled(state => !state)
    await getData();
    setApiCalled(state => !state)
  }

  const handleNextClick = () => {
    const nextItems = [...data];
    const poppedNews = nextItems.shift();  // Removes the first item from the array
    if (nextItems.length < 3 && !apiCalled){
      handleAddMoreRecommendation()
    }
    setData(nextItems);
    setPrevData((state) => ([...state, poppedNews]))
  }

  const handlePrevClick = () => {
    const prevItems = [...prevData]
    const popppedNews = prevItems.pop()
    setPrevData(prevItems)
    setData ((state) => ([popppedNews, ...state]))
  }

  if (loading) {
    return(
      <h4>Loading...</h4>
    )
    
  }

  return(
    <div>
    <h1>Hello</h1>
    {loggedIn ? (
      <Logout logout = {handleLogout} />
    ) : (
    <button><Link to = "/login-page">Login</Link></button>
    )}

    {data.length > 0 && (
            <div>
              <div><b>Title:</b> {data[0].title}</div>
              <div><b>Summary:</b>{data[0].summary}</div>
              <div><b>URL:</b><a href={data[0].url} target="_blank" rel="noopener noreferrer">URL</a></div>
              <br />
              {/* <button onClick={handleLike}>Like</button> */}
              <br />
              {
                (prevData.length > 0) && (
                  <button onClick={() => handlePrevClick()}>Prev</button>
                )
              }
              <button onClick={() => handleNextClick()}>Next</button>
            </div>
          )
    }
    </div>
  )
}

export default App
