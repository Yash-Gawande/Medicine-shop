import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { setAccessToken } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { RegisterPage } from "./register";

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/register"]}>
      <Routes>
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/account" element={<p>Account page</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

async function fill() {
  await userEvent.type(screen.getByLabelText("Full name"), "Asha Patil");
  await userEvent.type(screen.getByLabelText("Mobile number"), "98765 43210");
  await userEvent.type(screen.getByLabelText("Email"), "asha@example.com");
  await userEvent.type(screen.getByLabelText("Password"), "Passw0rd1");
}

beforeEach(() => {
  setAccessToken(null);
  useAuth.setState({ user: null, status: "anonymous" });
});
afterEach(() => vi.restoreAllMocks());

it("requires accepting the terms", async () => {
  const fetchMock = vi.spyOn(globalThis, "fetch");
  renderPage();
  await fill();
  await userEvent.click(screen.getByRole("button", { name: "Create account" }));
  expect(await screen.findByText("Please accept the Terms and Privacy Policy")).toBeInTheDocument();
  expect(fetchMock).not.toHaveBeenCalled();
});

it("registers with a cleaned mobile number and redirects", async () => {
  const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
    json(
      {
        access_token: "t",
        token_type: "bearer",
        expires_in: 900,
        user: { id: "u", email: "asha@example.com", mobile: "+919876543210", user_type: "customer", status: "pending_verification", is_email_verified: false, is_mobile_verified: false, roles: ["customer"], permissions: [] },
      },
      201,
    ),
  );
  renderPage();
  await fill();
  await userEvent.click(screen.getByRole("checkbox"));
  await userEvent.click(screen.getByRole("button", { name: "Create account" }));
  await waitFor(() => expect(screen.getByText("Account page")).toBeInTheDocument());
  const body = JSON.parse((fetchMock.mock.calls[0]![1] as RequestInit).body as string);
  expect(body).toEqual({ full_name: "Asha Patil", mobile: "9876543210", email: "asha@example.com", password: "Passw0rd1" });
});

it("toggles password visibility", async () => {
  renderPage();
  const input = screen.getByLabelText("Password");
  expect(input).toHaveAttribute("type", "password");
  await userEvent.click(screen.getByRole("button", { name: "Show password" }));
  expect(input).toHaveAttribute("type", "text");
});
