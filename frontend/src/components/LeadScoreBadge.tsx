interface LeadScoreBadgeProps {
  score: number;
  size?: 'sm' | 'md';
}

export default function LeadScoreBadge({ score, size = 'md' }: LeadScoreBadgeProps) {
  let colorClass: string;
  if (score >= 70) {
    colorClass = 'bg-green-100 text-green-800';
  } else if (score >= 40) {
    colorClass = 'bg-yellow-100 text-yellow-800';
  } else {
    colorClass = 'bg-red-100 text-red-800';
  }

  const sizeClass = size === 'sm'
    ? 'px-1.5 py-0.5 text-xs'
    : 'px-2 py-0.5 text-sm';

  return (
    <span className={`inline-flex items-center rounded-full font-semibold ${colorClass} ${sizeClass}`}>
      {score}
    </span>
  );
}
