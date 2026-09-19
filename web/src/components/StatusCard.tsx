type StatusCardProps = {
  label: string;
  value: string;
  detail: string;
};

export function StatusCard({ label, value, detail }: StatusCardProps) {
  return (
    <article className="rounded-2xl border border-ink/10 bg-white p-5 shadow-sm">
      <p className="text-sm font-medium text-ink/60">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
      <p className="mt-1 text-sm text-ink/60">{detail}</p>
    </article>
  );
}

