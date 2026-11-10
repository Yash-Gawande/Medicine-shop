import { createBrowserRouter } from "react-router";
import { RequireAuth } from "@/components/require-auth";
import { AccountPage } from "@/pages/account";
import { HomePage } from "@/pages/home";
import { LoginPage } from "@/pages/login";
import { NotFoundPage } from "@/pages/not-found";
import { RegisterPage } from "@/pages/register";

// Routes are added per phase: /products, /product/:slug, /cart, /checkout, ...
export const router = createBrowserRouter([
  { path: "/", element: <HomePage /> },
  { path: "/login", element: <LoginPage /> },
  { path: "/register", element: <RegisterPage /> },
  { element: <RequireAuth />, children: [{ path: "/account", element: <AccountPage /> }] },
  { path: "*", element: <NotFoundPage /> },
]);
