import { Link } from "react-router";

export function NotFoundPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="text-2xl font-semibold">Page not found</h1>
      <Link to="/" className="rounded-lg bg-primary px-4 py-2 text-primary-foreground hover:opacity-90">
        Go home
      </Link>
    </main>
  );
}
