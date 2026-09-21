// Placeholder wordmark until the real Ryde logo lands in src/assets/brand/.
export default function Header() {
  return (
    <header className="flex items-center gap-2 border-b border-ryde-light px-6 py-4">
      <span className="text-2xl font-extrabold tracking-tight text-ryde">
        ryde<span className="text-ryde-dark">.</span>
      </span>
      <span className="text-sm text-gray-500">Dispute Resolution</span>
    </header>
  );
}
