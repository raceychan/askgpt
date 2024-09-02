// import React from 'react';

// import {Link, ErrorComponent } from "@tanstack/react-router"
// import { Button } from "@/components/ui/button"

// interface RouteError {
//   statusText?: string;
//   message?: string;
// }

// const ErrorPage: React.FC = () => {
//   const error = ErrorComponent() as RouteError;
//   console.error(error);

//   return (
//     <div id="error-page" className="flex flex-col items-center justify-center min-h-screen text-center">
//       <h1 className="text-4xl font-bold mb-4">Oops!</h1>
//       <p className="mb-2">Sorry, an unexpected error has occurred.</p>
//       <p className="mb-6">
//         <i>{error.statusText || error.message}</i>
//       </p>
//       <Button asChild  className="w-50 border-2 border-primary">
//         <Link to="/">Go to Home</Link>
//       </Button>
//     </div>
//   );
// }

// export default ErrorPage;