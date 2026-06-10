import React from 'react';
import { TableRow, TableCell, Stack, Typography } from '@mui/material';

interface DataTableEmptyProps {
	colSpan: number;
	message?: string;
	subMessage?: string;
}

/**
 * Modular empty state component for DataTable.
 * Displayed when no records match the current filters or search.
 */
const DataTableEmpty: React.FC<DataTableEmptyProps> = ({ 
	colSpan, 
	message = 'No records found',
	subMessage = 'Try adjusting your filters or search terms'
}) => {
	return (
		<TableRow>
			<TableCell colSpan={colSpan} align="center" sx={{ py: 10 }}>
				<Stack component="div" spacing={1} sx={{ alignItems: 'center' }}>
					<Typography variant="h6" color="text.secondary" sx={{ fontWeight: 600 }}>
						{message}
					</Typography>
					{subMessage && (
						<Typography variant="body2" color="text.disabled">
							{subMessage}
						</Typography>
					)}
				</Stack>
			</TableCell>
		</TableRow>
	);
};

export default DataTableEmpty;
