import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider, createBrowserRouter } from 'react-router-dom';
import App from '@/app/App.tsx'
import HomePage from '@/pages/HomePage.tsx'
import AuthenticationPage from '@/pages/AuthentificationPage.tsx'
import ErrorPage from '@/pages/ErrorPage.tsx'
import '@/index.css'

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    errorElement: <ErrorPage />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'login', element: <AuthenticationPage /> },
    ],
  },
]);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
)
