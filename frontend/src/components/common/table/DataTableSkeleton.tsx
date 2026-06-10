import React from 'react';
import { TableRow, TableCell, Skeleton } from '@mui/material';

interface ColumnDef {
	id: string | number | symbol;
	align?: 'left' | 'right' | 'center';
	hideOnMobile?: boolean;
}

interface DataTableSkeletonProps {
	columns: ColumnDef[];
	rowsPerPage: number;
}

/**
 * Modular skeleton loader for DataTable.
 * Renders cell-by-cell skeletons based on column definitions for a premium "SaaS" feel.
 */
const DataTableSkeleton: React.FC<DataTableSkeletonProps> = ({ columns, rowsPerPage }) => {
	return (
		<>
			{Array.from(new Array(rowsPerPage)).map((_, index) => (
				<TableRow key={`skeleton-${index}`}>
					{columns.map((col, colIdx) => (
						<TableCell 
							key={`skeleton-cell-${colIdx}`} 
							align={col.align || 'left'}
							sx={{ display: col.hideOnMobile ? { xs: 'none', md: 'table-cell' } : 'table-cell' }}
						>
							<Skeleton 
								variant="text" 
								width={col.id === 'actions' ? 60 : '80%'} 
								height={24} 
								sx={{ 
									ml: col.align === 'right' ? 'auto' : 0,
									mr: col.align === 'center' ? 'auto' : 0
								}} 
							/>
						</TableCell>
					))}
				</TableRow>
			))}
		</>
	);
};

export default DataTableSkeleton;
