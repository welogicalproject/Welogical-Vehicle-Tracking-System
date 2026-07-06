export function formatDate(value?: string | null): string {
  if (!value) return "Never";
  // Append Z to UTC timestamp strings if not present to ensure standard parsing
  const cleanValue = value.endsWith("Z") ? value : `${value}Z`;
  const date = new Date(cleanValue);
  
  // Check if date is valid
  if (isNaN(date.getTime())) {
    return "Invalid Date";
  }
  
  return date.toLocaleString();
}
