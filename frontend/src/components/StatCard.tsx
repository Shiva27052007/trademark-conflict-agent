interface Props {
  label: string;
  value: string | number;
  icon: string;
  trend?: string;
  color?: string;
}

export default function StatCard({ label, value, icon, trend, color = 'cyan' }: Props) {
  const colorMap: Record<string, string> = {
    cyan: 'from-cyan-500/20 to-cyan-600/5 border-cyan-500/20',
    blue: 'from-blue-500/20 to-blue-600/5 border-blue-500/20',
    red: 'from-red-500/20 to-red-600/5 border-red-500/20',
    yellow: 'from-yellow-500/20 to-yellow-600/5 border-yellow-500/20',
    green: 'from-green-500/20 to-green-600/5 border-green-500/20',
  };

  return (
    <div className={`bg-gradient-to-br ${colorMap[color] || colorMap.cyan} border rounded-xl p-5 animate-fade-in`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-400 mb-1">{label}</p>
          <p className="text-3xl font-bold text-white">{value}</p>
          {trend && <p className="text-xs text-gray-500 mt-1">{trend}</p>}
        </div>
        <div className="text-2xl">{icon}</div>
      </div>
    </div>
  );
}
