/**
 * Hook for standardized date and time formatting across the application.
 * Date format: DD-MMM-YYYY (e.g., 25-Apr-2026)
 * Time format: 12-hour IST (e.g., 03:12 PM)
 */
export const useDateTime = () => {
	
	/**
	 * Formats a date into DD-MMM-YYYY
	 * @param date Date object, ISO string, or timestamp
	 * @returns Formatted date string or '-' if invalid
	 */
	const formatDate = (date: Date | string | number | null | undefined): string => {
		if (!date) return '-';
		
		const dateObj = new Date(date);
		if (isNaN(dateObj.getTime())) return '-';
		
		const day = String(dateObj.getDate()).padStart(2, '0');
		const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
		const month = monthNames[dateObj.getMonth()];
		const year = dateObj.getFullYear();
		
		return `${day}-${month}-${year}`;
	};

	/**
	 * Formats a time into 12-hour format (hh:mm a)
	 * @param date Date object, ISO string, or timestamp
	 * @returns Formatted time string or '-' if invalid
	 */
	const formatTime = (date: Date | string | number | null | undefined): string => {
		if (!date) return '-';
		
		const dateObj = new Date(date);
		if (isNaN(dateObj.getTime())) return '-';
		
		let hours = dateObj.getHours();
		const minutes = String(dateObj.getMinutes()).padStart(2, '0');
		const ampm = hours >= 12 ? 'PM' : 'AM';
		hours = hours % 12;
		hours = hours ? hours : 12; // the hour '0' should be '12'
		const strHours = String(hours).padStart(2, '0');

		return `${strHours}:${minutes} ${ampm}`;
	};

	/**
	 * Formats both date and time
	 * @param date Date object, ISO string, or timestamp
	 * @returns Formatted string (e.g., 25-Apr-2026 03:12 PM)
	 */
	const formatDateTime = (date: Date | string | number | null | undefined): string => {
		if (!date) return '-';
		
		const dateObj = new Date(date);
		if (isNaN(dateObj.getTime())) return '-';
		
		const fDate = formatDate(dateObj);
		const fTime = formatTime(dateObj);
		
		if (fDate === '-' || fTime === '-') return '-';
		
		return `${fDate} ${fTime}`;
	};

	return {
		formatDate,
		formatTime,
		formatDateTime
	};
};

export default useDateTime;
