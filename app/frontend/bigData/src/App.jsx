import { useEffect, useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import Logout from "./components/logout";
import API from "./assets/api";
import "./css/App.css"; // Import the CSS file
function App() {
  const defaultFeedback = {
    article : "",
    readTime : "",
    reaction : 0,
    clickedUrl : 0,
    length : ""
  }
  const [rec, setRec] = useState(0);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loggedIn, setLoggedIn] = useState(false);
  const [apiCalled, setApiCalled] = useState(false);
  const [allfeedBack, setAllFeedBack] = useState([]);
  const [feedBack, setFeedBack] = useState(defaultFeedback);
  const [startTime, setStartTime] = useState("")

  // article, read_time, reaction, clicked_url, length
  const getData = async () => {
    try {
      const response = await axios.get(
        `${API}/recommendations/?prev_rec=${rec}`,
        {
          withCredentials: true,
        }
      );
      if (data.length === 0) {
        setFeedBack((state) => ({
          ...state,
        ['article'] :response.data.recommendations[0]._id,
        ['length'] : response.data.recommendations[0].summary.length
        }))
        setStartTime(Date.now())
      }
      setData((currentState) => [
        ...currentState,
        ...response.data.recommendations,
      ]);
      setRec(response.data.page);
      setLoggedIn(response.data.loggedIn);

    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      if (loading) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    const callGetData = async () => {
      await getData()
    };
    callGetData();
  }, []);

  const sendFeedBack = async() => {
      const formData = new FormData()
      // const object = allfeedBack.map(obj => [obj.article, obj.readTime, obj.reaction, obj.clickedUrl, obj.length])
      formData.append('activity', JSON.stringify(allfeedBack))
      try {
        await axios.post(`${API}/update-user-activity`, formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
          withCredentials: true,
        })
        setAllFeedBack([])
      } catch (error) {
        console.log(error);
      }
  }

  const handleFeedBackPush = () =>{
    const readTime = Date.now() - startTime
    setStartTime(Date.now())
    const feedbackExists = allfeedBack.some(item => item.article === feedBack.article);
    if (!feedbackExists) {  
      setAllFeedBack(state => [...state, {...feedBack, ['readTime'] : readTime / 1000}]);
    }
    if (allfeedBack.length > 7) {
      sendFeedBack();
    }
    setFeedBack(defaultFeedback)
  }

  const handleLogout = async () => {
    setLoggedIn(false);
    setRec(0);
    setData([]);
    setLoading(true);
    handleFeedBackPush();
    await getData();
    setLoading(false);
  };

  const handleAddMoreRecommendation = async () => {
    setApiCalled((state) => !state);
    await getData();
    setApiCalled((state) => !state);
  };

  const handleNextClick = () => {
    handleFeedBackPush()
    const nextItems = [...data];
    nextItems.shift(); 
    if (nextItems.length < 4 && !apiCalled) {
      handleAddMoreRecommendation();
    }
    setFeedBack((state) => ({
      ...state,
      ['article'] : nextItems[0]._id,
      ['length'] : nextItems[0].summary.length
    }))
    setData(nextItems);
  };

  const handleFeedBack = (index, value) => {
    setFeedBack((state) => ({...state, [index] : value}))
  };

  if (loading) {
    return <h4 className="loading">Loading...</h4>;
  }
  return (
    <div className="app-container">
      <h1 className="app-header">PrimePicks</h1>
      {loggedIn ? (
        <Logout logout={handleLogout} />
      ) : (
        <button className="login-button">
          <Link to="/login-page">Login</Link>
        </button>
      )}

      <br />
      {loggedIn && (
        <button className="login-button">
          <Link to="/keyword-search">Search Keyword</Link>
        </button>
      )}
      <br />
      {loggedIn && (
        <button className="login-button">
          <Link to="/search">Search</Link>
        </button>
      )}

      {data.length > 0 && (
        <div className="recommendation-card">
          <div>
            <b>Title:</b> {data[0].title}
          </div>
          <div>
            <b>Summary:</b>
            {data[0].summary}
          </div>
          <div>
            <b>URL:</b>
            <a onClick={(e) => handleFeedBack('clickedUrl', 1)} href={data[0].url} target="_blank" rel="noopener noreferrer">
              URL
            </a>
          </div>
          <div className="navigation-buttons">
            {/* <button className="like-button">Like</button> */}
            <button onClick={() => handleNextClick()}>Next</button>
          </div>
          <div className="like-dislike-buttons">
            <button
              onClick={(e) => handleFeedBack('reaction', 1 - feedBack['reaction'] )}
            >
              Like
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
