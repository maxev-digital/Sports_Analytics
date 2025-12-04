interface PropTypeTabsProps {
  propTypes: string[];
  selectedPropType: string;
  onSelectPropType: (type: string) => void;
  formatPropType: (type: string) => string;
}

export function PropTypeTabs({ propTypes, selectedPropType, onSelectPropType, formatPropType }: PropTypeTabsProps) {
  if (propTypes.length === 0) return null;

  return (
    <div className="mb-4 flex flex-wrap gap-2 bg-slate-800/50 border border-slate-700 p-3 rounded-lg">
      <button
        onClick={() => onSelectPropType('all')}
        className={`px-6 py-2.5 text-base font-bold transition-all rounded ${
          selectedPropType === 'all'
            ? 'bg-blue-600 text-white shadow-lg'
            : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
        }`}
      >
        ALL PROPS
      </button>
      {propTypes.map((type) => (
        <button
          key={type}
          onClick={() => onSelectPropType(type)}
          className={`px-6 py-2.5 text-base font-bold transition-all rounded whitespace-nowrap ${
            selectedPropType === type
              ? 'bg-blue-600 text-white shadow-lg'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          {formatPropType(type).toUpperCase()}
        </button>
      ))}
    </div>
  );
}
