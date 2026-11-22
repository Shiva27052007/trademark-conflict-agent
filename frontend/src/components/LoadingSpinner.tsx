export default function LoadingSpinner({ message = 'Processing...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="relative">
        <div className="w-12 h-12 border-4 border-charcoal-700 rounded-full"></div>
        <div className="w-12 h-12 border-4 border-transparent border-t-cyan-400 rounded-full absolute top-0 left-0 animate-spin"></div>
      </div>
      <p className="mt-4 text-gray-400 text-sm">{message}</p>
    </div>
  );
}
