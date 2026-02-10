export function Spinner({
  size = "md",
  color = "currentColor",
}: {
  size?: "sm" | "md" | "lg";
  color?: string;
}) {
  const sizeClasses = {
    sm: "w-4 h-4 border-2",
    md: "w-6 h-6 border-2",
    lg: "w-8 h-8 border-3",
  };

  return (
    <div
      className={`animate-spin rounded-full ${sizeClasses[size]} border-solid border-t-transparent`}
      style={{ borderColor: color }}
      aria-label="Loading"
      role="status"
    />
  );
}
