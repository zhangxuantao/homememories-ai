interface YearPillsProps {
  years: number[];
  selectedYear: number | null;
  onSelect: (year: number) => void;
}

export default function YearPills({ years, selectedYear, onSelect }: YearPillsProps) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-2 px-4" style={{ scrollbarWidth: 'none' }}>
      {years.map((year) => (
        <button
          key={year}
          onClick={() => onSelect(year)}
          className={`flex-shrink-0 px-4 py-1.5 rounded-pill text-sm font-medium transition-colors ${
            selectedYear === year
              ? 'bg-primary text-white'
              : 'bg-misty text-text hover:bg-subtle'
          }`}
        >
          {year}
        </button>
      ))}
    </div>
  );
}
