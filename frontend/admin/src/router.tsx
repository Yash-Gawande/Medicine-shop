import { createBrowserRouter } from "react-router";
import { AdminLayout } from "@/components/admin-layout";
import { RequireStaff } from "@/components/require-staff";
import { HomePage } from "@/pages/home";
import { LoginPage } from "@/pages/login";
import { NotFoundPage } from "@/pages/not-found";

// Served under /admin in production (see vite `base` + nginx config).
export const router = createBrowserRouter(
  [
    { path: "/login", element: <LoginPage /> },
    {
      element: <RequireStaff />,
      children: [{ element: <AdminLayout />, children: [{ path: "/", element: <HomePage /> }] }],
    },
    { path: "*", element: <NotFoundPage /> },
  ],
  { basename: import.meta.env.BASE_URL },
);
