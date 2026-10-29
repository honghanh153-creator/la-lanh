/** Shared date checks for first entry and correction (US-02, US-23 D6). */

export function validDate(day: string, month: string, year: string): string | null {
  if (!/^\d{1,2}$/.test(day) || !/^\d{1,2}$/.test(month) || !/^\d{4}$/.test(year)) {
    return null;
  }
  const numericDay = Number(day);
  const numericMonth = Number(month);
  const numericYear = Number(year);
  const value = new Date(Date.UTC(numericYear, numericMonth - 1, numericDay));
  if (
    numericYear < new Date().getFullYear() - 120 || numericYear > new Date().getFullYear()
    || value.getUTCFullYear() !== numericYear
    || value.getUTCMonth() !== numericMonth - 1
    || value.getUTCDate() !== numericDay
    || value > new Date()
  ) return null;
  return `${year}-${month.padStart(2, "0")}-${day.padStart(2, "0")}`;
}

export function isUnder18(birthDate: string): boolean {
  const birth = new Date(`${birthDate}T00:00:00.000Z`);
  const today = new Date();
  let age = today.getUTCFullYear() - birth.getUTCFullYear();
  const monthDelta = today.getUTCMonth() - birth.getUTCMonth();
  const birthdayNotReached = monthDelta < 0
    || (monthDelta === 0 && today.getUTCDate() < birth.getUTCDate());
  if (birthdayNotReached) age -= 1;
  return age < 18;
}
