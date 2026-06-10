import React from 'react';
import {
	Paper,
	Table,
	TableBody,
	TableContainer,
	useTheme
} from '@mui/material';
import CustomTablePagination from './CustomTablePagination';
import DataTableHeader from './DataTableHeader';
import DataTableHead from './DataTableHead';
import DataTableEmpty from './DataTableEmpty';
import DataTableSkeleton from './DataTableSkeleton';

import type { DataTableHeaderProps } from './DataTableHeader';
import type { ColumnDefinition } from './DataTableHead';

export type { ColumnDefinition };

export interface DataTableProps<T> extends DataTableHeaderProps {
	columns: ColumnDefinition<T>[];
	data: T[];
	totalCount: number;
	page: number;
	rowsPerPage: number;
	onPageChange: (event: unknown, newPage: number) => void;
	onRowsPerPageChange: (newRowsPerPage: number) => void;
	orderBy?: keyof T;
	order?: 'asc' | 'desc';
	onSortRequest?: (property: keyof T) => void;
	emptyMessage?: string;
	renderRow: (item: T) => React.ReactNode;
	// Selection support
	numSelected?: number;
	onSelectAllClick?: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

const DataTable = <T,>({
	columns,
	data,
	loading,
	totalCount,
	page,
	rowsPerPage,
	onPageChange,
	onRowsPerPageChange,
	searchTerm = '',
	onSearchChange,
	searchPlaceholder,
	orderBy,
	order = 'asc',
	onSortRequest,
	onRefresh,
	onFilterOpen,
	activeFilterCount,
	onCreateClick,
	createButtonText,
	canCreate,
	headerActions,
	emptyMessage = 'No records found',
	renderRow,
	numSelected,
	onSelectAllClick
}: DataTableProps<T>) => {
	const theme = useTheme();
	const visibleColumns = columns.filter(col => !col.hidden);
	const columnCount = visibleColumns.length + (onSelectAllClick ? 1 : 0);

	return (
		<Paper sx={{
			border: `1px solid ${theme.palette.divider}`,
			boxShadow: 'none',
			borderRadius: `${theme.shape.borderRadius}px`,
			overflow: 'hidden',
			bgcolor: theme.palette.background.paper
		}}>
			<DataTableHeader
				searchTerm={searchTerm}
				onSearchChange={onSearchChange}
				searchPlaceholder={searchPlaceholder}
				activeFilterCount={activeFilterCount}
				onFilterOpen={onFilterOpen}
				onRefresh={onRefresh}
				onCreateClick={onCreateClick}
				createButtonText={createButtonText}
				canCreate={canCreate}
				loading={loading}
				headerActions={headerActions}
			/>

			<TableContainer sx={{ overflowX: 'auto', WebkitOverflowScrolling: 'touch' }}>
				<Table sx={{ minWidth: 650 }}>
					<DataTableHead
						columns={columns}
						orderBy={orderBy}
						order={order}
						onSortRequest={onSortRequest}
						numSelected={numSelected}
						onSelectAllClick={onSelectAllClick}
						rowCount={data.length}
					/>
					<TableBody 
						aria-busy={loading}
						sx={{
							opacity: loading ? 0.65 : 1,
							transition: 'opacity 0.2s',
							pointerEvents: loading ? 'none' : 'auto'
						}}
					>
						{loading && data.length === 0 ? (
							<DataTableSkeleton
								columns={visibleColumns}
								rowsPerPage={rowsPerPage || 5}
							/>
						) : data.length === 0 ? (
							<DataTableEmpty
								colSpan={columnCount}
								message={emptyMessage}
							/>
						) : (
							data.map(renderRow)
						)}
					</TableBody>
				</Table>
			</TableContainer>

			<CustomTablePagination
				count={totalCount}
				page={page}
				rowsPerPage={rowsPerPage}
				onPageChange={onPageChange}
				onRowsPerPageChange={(e) => onRowsPerPageChange(parseInt(e.target.value, 10))}
				onRowsPerPageSelectChange={onRowsPerPageChange}
			/>
		</Paper>
	);
};

export default DataTable;
