type ClassValue = string | number | null | undefined | boolean | { [key: string]: boolean } | ClassValue[];

export function cn(...classes: ClassValue[]): string {
  const result: string[] = [];
  
  for (const cls of classes) {
    if (!cls) continue;
    
    if (typeof cls === 'string') {
      result.push(cls);
    } else if (typeof cls === 'object' && !Array.isArray(cls)) {
      for (const [key, value] of Object.entries(cls)) {
        if (value) {
          result.push(key);
        }
      }
    } else if (Array.isArray(cls)) {
      result.push(cn(...cls));
    }
  }
  
  return result.join(' ');
}