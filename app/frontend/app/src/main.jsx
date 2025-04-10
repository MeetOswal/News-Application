import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider, createBrowserRouter } from "react-router-dom";
import App from './App';
import LoginPage from './components/login';
import CreateUser from './components/createUser';
import AddKeywords from './components/addKeywords';
import Search from './components/search';
const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
  },
  {
    path : "/login-page",
    element : <LoginPage />
  },
  {
    path : "/register",
    element : <CreateUser />
  },{
    path: "keyword-search",
    element : <AddKeywords />
  },
  {
    path : "/search",
    element : <Search />
  }
]);

createRoot(document.getElementById('root')).render(
  <RouterProvider router={router} />
)
