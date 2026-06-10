import React, { memo } from 'react';
import {
	Box,
	TextField,
	Button,
	InputAdornment,
	Badge,
	useTheme,
	Tooltip,
	alpha
} from '@mui/material';
import { Search, FilterList, Refresh, Add } from '@mui/icons-material';

export interface DataTableHeaderProps {
	searchTerm: string;
	onSearchChange?: (value: string) => void;
	searchPlaceholder?: string;
	activeFilterCount?: number;
	onFilterOpen?: (event: React.MouseEvent<HTMLButtonElement>) => void;
	onRefresh?: () => void;
	onCreateClick?: () => void;
	createButtonText?: string;
	canCreate?: boolean;
	loading?: boolean;
	headerActions?: React.ReactNode;
}

const DataTableHeader: React.FC<DataTableHeaderProps> = memo(({
	searchTerm,
	onSearchChange,
	searchPlaceholder = 'Search...',
	activeFilterCount = 0,
	onFilterOpen,
	onRefresh,
	onCreateClick,
	createButtonText = 'Create',
	canCreate = false,
	loading = false,
	headerActions
}) => {
	const theme = useTheme();

	return (
		<Box sx={{
			p: 2,
			display: 'flex',
			flexDirection: { xs: 'column', sm: 'row' },
			justifyContent: 'space-between',
			alignItems: { xs: 'stretch', sm: 'center' },
			borderBottom: `1px solid ${theme.palette.divider}`,
			gap: 2
		}}>
			<Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, flex: 1, gap: 2, alignItems: { xs: 'stretch', sm: 'center' } }}>
				{onSearchChange && (
					<TextField
						placeholder={searchPlaceholder}
						value={searchTerm}
						onChange={(e) => onSearchChange(e.target.value)}
						size="small"
						fullWidth
						slotProps={{
							htmlInput: {
								autoComplete: 'off',
								name: 'enterprise-table-search'
							},
							input: {
								startAdornment: (
									<InputAdornment position="start">
										<Search sx={{ color: 'text.secondary', fontSize: 20 }} />
									</InputAdornment>
								),
							}
						}}
						sx={{
							maxWidth: { xs: '100%', sm: '350px' },
							'& .MuiOutlinedInput-root': {
								bgcolor: theme.palette.background.paper,
								'& fieldset': { borderColor: theme.palette.divider },
								'&:hover fieldset': { borderColor: theme.palette.primary.main },
							}
						}}
					/>
				)}
				{headerActions}
			</Box>

			<Box sx={{ display: 'flex', gap: 1, justifyContent: { xs: 'space-between', sm: 'flex-end' } }}>
				<Box sx={{ display: 'flex', gap: 1 }}>
					{onRefresh && (
						<Tooltip title="Refresh data">
							<Button
								variant="outlined"
								startIcon={<Refresh className={loading ? 'spin-animation' : ''} />}
								onClick={onRefresh}
								disabled={loading}
								sx={{
									textTransform: 'none',
									color: theme.palette.text.primary,
									borderColor: theme.palette.divider,
									'&:hover': {
										borderColor: theme.palette.text.primary,
										bgcolor: alpha(theme.palette.primary.main, 0.05)
									}
								}}
							>
								Refresh
							</Button>
						</Tooltip>
					)}

					{onFilterOpen && (
						<Badge badgeContent={activeFilterCount} color="primary">
							<Button
								variant="outlined"
								startIcon={<FilterList fontSize="small" />}
								onClick={onFilterOpen}
								sx={{
									textTransform: 'none',
									color: theme.palette.text.primary,
									borderColor: theme.palette.divider,
									'&:hover': {
										borderColor: theme.palette.text.primary,
										bgcolor: alpha(theme.palette.primary.main, 0.05)
									}
								}}
							>
								Filters
							</Button>
						</Badge>
					)}
				</Box>

				{canCreate && onCreateClick && (
					<Button
						variant="contained"
						startIcon={<Add />}
						onClick={onCreateClick}
						sx={{
							color: 'white',
							textTransform: 'none',
							fontWeight: 600,
							'&:hover': {
								bgcolor: theme.palette.primary.dark,
							}
						}}
					>
						{createButtonText}
					</Button>
				)}
			</Box>
			<style>
				{`
					@keyframes spin {
						from { transform: rotate(0deg); }
						to { transform: rotate(360deg); }
					}
					.spin-animation {
						animation: spin 1s linear infinite;
					}
				`}
			</style>
		</Box>
	);
});

DataTableHeader.displayName = 'DataTableHeader';

export default DataTableHeader;
