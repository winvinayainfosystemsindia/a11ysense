import React from 'react';
import {
	TableHead,
	TableRow,
	TableCell,
	TableSortLabel,
	Checkbox,
	useTheme
} from '@mui/material';

export interface ColumnDefinition<T> {
	id: keyof T | 'actions';
	label: string;
	sortable?: boolean;
	align?: 'left' | 'right' | 'center';
	width?: string | number;
	hidden?: boolean;
	hideOnMobile?: boolean;
}

interface DataTableHeadProps<T> {
	columns: ColumnDefinition<T>[];
	orderBy?: keyof T;
	order?: 'asc' | 'desc';
	onSortRequest?: (property: keyof T) => void;
	// Selection support
	numSelected?: number;
	onSelectAllClick?: (event: React.ChangeEvent<HTMLInputElement>) => void;
	rowCount?: number;
}

/**
 * Modular TableHead component for DataTable.
 * Manages column rendering, sorting labels, and optional selection checkboxes.
 */
const DataTableHead = <T,>({
	columns,
	orderBy,
	order = 'asc',
	onSortRequest,
	numSelected = 0,
	onSelectAllClick,
	rowCount = 0
}: DataTableHeadProps<T>) => {
	const theme = useTheme();
	const visibleColumns = columns.filter(col => !col.hidden);
	const isAllSelected = rowCount > 0 && numSelected === rowCount;
	const isSomeSelected = numSelected > 0 && numSelected < rowCount;

	return (
		<TableHead>
			<TableRow sx={{ bgcolor: theme.palette.background.default }}>
				{onSelectAllClick && (
					<TableCell padding="checkbox" sx={{ borderBottom: `2px solid ${theme.palette.divider}`, py: 1.5 }}>
						<Checkbox
							indeterminate={isSomeSelected}
							checked={isAllSelected}
							onChange={onSelectAllClick}
							size="small"
						/>
					</TableCell>
				)}
				{visibleColumns.map((column) => (
					<TableCell
						key={String(column.id)}
						align={column.align || 'left'}
						style={{ width: column.width }}
						sx={{
							fontWeight: 700,
							color: theme.palette.text.secondary,
							whiteSpace: 'nowrap',
							fontSize: '0.75rem',
							textTransform: 'uppercase',
							letterSpacing: '0.05em',
							borderBottom: `2px solid ${theme.palette.divider}`,
							py: 1.5,
							display: column.hideOnMobile ? { xs: 'none', md: 'table-cell' } : 'table-cell'
						}}
					>
						{column.sortable && onSortRequest ? (
							<TableSortLabel
								active={orderBy === column.id}
								direction={orderBy === column.id ? order : 'asc'}
								onClick={() => onSortRequest(column.id as keyof T)}
								sx={{
									'&.Mui-active': {
										fontWeight: 800,
										color: theme.palette.text.primary
									},
									'& .MuiTableSortLabel-icon': { fontSize: 16 }
								}}
							>
								{column.label}
							</TableSortLabel>
						) : (
							column.label
						)}
					</TableCell>
				))}
			</TableRow>
		</TableHead>
	);
};

export default DataTableHead;
