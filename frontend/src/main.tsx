import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider, createBrowserRouter } from 'react-router-dom';
import App from './App.tsx'
// import HomePage from './pages/HomePage.tsx'
import AuthenticationPage from './pages/AuthentificationPage.tsx'
import './index.css'

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    errorElement: <div> 404 NOT Found </div>,
  },
  { path: '/login', element: <AuthenticationPage /> },
]);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
)
