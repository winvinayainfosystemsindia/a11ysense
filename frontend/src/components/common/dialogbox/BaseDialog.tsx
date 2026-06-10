import React from 'react';
import {
	Dialog,
	DialogTitle,
	DialogContent,
	DialogActions,
	Typography,
	IconButton,
	Box,
	alpha,
	useTheme
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import type { BaseDialogProps } from './types';

const BaseDialog: React.FC<BaseDialogProps> = ({
	open,
	onClose,
	title,
	subtitle,
	children,
	actions,
	maxWidth = 'sm',
	fullWidth = true,
	loading = false,
	showCloseButton = true
}) => {
	const theme = useTheme();

	return (
		<Dialog
			open={open}
			onClose={loading ? undefined : onClose}
			maxWidth={maxWidth}
			fullWidth={fullWidth}
			slotProps={{
				paper: {
					sx: {
						borderRadius: '6px',
						boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
						border: `1px solid ${theme.palette.divider}`,
						overflow: 'hidden'
					}
				}
			}}
		>
			<DialogTitle sx={{ 
				p: 3, 
				pb: subtitle ? 1 : 2,
				display: 'flex', 
				justifyContent: 'space-between', 
				alignItems: 'flex-start',
				bgcolor: alpha(theme.palette.background.default, 0.5)
			}}>
				<Box>
					<Typography variant="h6" sx={{ fontWeight: 700, color: 'text.primary', lineHeight: 1.2 }}>
						{title}
					</Typography>
					{subtitle && (
						<Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 500, mt: 0.5, display: 'block' }}>
							{subtitle}
						</Typography>
					)}
				</Box>
				{showCloseButton && (
					<IconButton 
						onClick={onClose} 
						disabled={loading}
						size="small" 
						sx={{ 
							color: 'text.secondary',
							transition: 'all 0.2s',
							'&:hover': { color: 'error.main', bgcolor: alpha(theme.palette.error.main, 0.05) }
						}}
					>
						<CloseIcon fontSize="small" />
					</IconButton>
				)}
			</DialogTitle>

			<DialogContent sx={{ p: 3, py: 1 }}>
				<Box sx={{ py: 2 }}>
					{children}
				</Box>
			</DialogContent>

			{actions && (
				<DialogActions sx={{ 
					p: 3, 
					pt: 1, 
					borderTop: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
					bgcolor: alpha(theme.palette.background.default, 0.3)
				}}>
					{actions}
				</DialogActions>
			)}
		</Dialog>
	);
};

export default BaseDialog;
