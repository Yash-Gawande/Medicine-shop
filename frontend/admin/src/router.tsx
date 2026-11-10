import { createBrowserRouter } from "react-router";
import { HomePage } from "@/pages/home";
import { NotFoundPage } from "@/pages/not-found";

// Served under /admin in production (see vite `base` + nginx config).
export const router = createBrowserRouter(
  [
    { path: "/", element: <HomePage /> },
    { path: "*", element: <NotFoundPage /> },
  ],
  { basename: import.meta.env.BASE_URL },
);
