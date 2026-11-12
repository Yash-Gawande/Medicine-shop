/** Decorative brand artwork: medical cross with capsules. Palette tokens only. */
export function AuthIllustration({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 480 290" className={className} role="img" aria-label="" aria-hidden>
      <circle cx="250" cy="140" r="128" fill="none" stroke="var(--primary)" strokeOpacity="0.35" strokeWidth="1.5" />
      <circle cx="250" cy="140" r="108" fill="var(--primary)" />
      <rect x="198" y="118" width="100" height="44" rx="8" fill="var(--background)" />
      <rect x="228" y="88" width="40" height="104" rx="8" fill="var(--background)" />
      {/* round tablet */}
      <circle cx="40" cy="60" r="26" fill="var(--muted)" />
      <rect x="14" y="56" width="52" height="8" fill="var(--foreground)" fillOpacity="0.25" />
      {/* capsule, left */}
      <g transform="rotate(-30 85 160)">
        <rect x="30" y="135" width="110" height="50" rx="25" fill="var(--primary)" />
        <path d="M85 135h30a25 25 0 0 1 0 50H85z" fill="var(--background)" />
      </g>
      {/* capsule, bottom right */}
      <g transform="rotate(-35 400 245)">
        <rect x="355" y="228" width="90" height="42" rx="21" fill="var(--primary)" />
        <path d="M355 249a21 21 0 0 1 21-21h24v42h-24a21 21 0 0 1-21-21z" fill="var(--muted)" />
      </g>
    </svg>
  );
}
