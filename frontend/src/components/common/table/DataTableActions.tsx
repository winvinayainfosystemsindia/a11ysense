import React, { useState, memo } from 'react';
import {
	IconButton,
	Menu,
	MenuItem,
	ListItemIcon,
	ListItemText,
	Tooltip,
	Typography,
	useTheme
} from '@mui/material';
import { MoreVert } from '@mui/icons-material';

export interface TableMenuAction<T> {
	label: string;
	icon?: React.ReactNode;
	onClick: (item: T) => void;
	color?: string;
	divider?: boolean;
	disabled?: boolean;
	hidden?: boolean;
}

interface DataTableActionsProps<T> {
	item: T;
	actions: TableMenuAction<T>[];
	tooltipTitle?: string;
	menuId?: string;
}

const DataTableActions = <T,>({
	item,
	actions,
	tooltipTitle = 'Actions',
	menuId = 'data-table-actions-menu'
}: DataTableActionsProps<T>) => {
	const theme = useTheme();
	const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
	const open = Boolean(anchorEl);

	const handleClick = (event: React.MouseEvent<HTMLElement>) => {
		event.stopPropagation();
		setAnchorEl(event.currentTarget);
	};

	const handleClose = () => {
		setAnchorEl(null);
	};

	const handleAction = (onClick: (item: T) => void) => {
		onClick(item);
		handleClose();
	};

	const visibleActions = actions.filter(action => !action.hidden);

	if (visibleActions.length === 0) return null;

	return (
		<>
			<Tooltip title={tooltipTitle}>
				<IconButton
					size="small"
					onClick={handleClick}
					aria-controls={open ? menuId : undefined}
					aria-haspopup="true"
					aria-expanded={open ? 'true' : undefined}
					sx={{ color: 'text.secondary' }}
				>
					<MoreVert fontSize="small" />
				</IconButton>
			</Tooltip>
			<Menu
				anchorEl={anchorEl}
				id={menuId}
				open={open}
				onClose={handleClose}
				onClick={handleClose}
				transformOrigin={{ horizontal: 'right', vertical: 'top' }}
				anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
				slotProps={{
					paper: {
						elevation: 2,
						sx: {
							minWidth: 160,
							border: `1px solid ${theme.palette.divider}`,
							'& .MuiMenuItem-root': {
								px: 1.5,
								py: 1,
							}
						}
					}
				}}
			>
				{visibleActions.map((action, index) => (
					<MenuItem
						key={`${action.label}-${index}`}
						onClick={() => handleAction(action.onClick)}
						disabled={action.disabled}
						divider={action.divider}
						sx={{ color: action.color }}
					>
						{action.icon && (
							<ListItemIcon sx={{ color: action.color || 'inherit' }}>
								{action.icon}
							</ListItemIcon>
						)}
						<ListItemText>
							<Typography variant="body2" color={action.color || 'inherit'}>
								{action.label}
							</Typography>
						</ListItemText>
					</MenuItem>
				))}
			</Menu>
		</>
	);
};

export default memo(DataTableActions) as typeof DataTableActions;
