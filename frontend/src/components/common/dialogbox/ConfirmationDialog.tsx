import React from 'react';
import { Button, Typography, Box, alpha, useTheme, CircularProgress } from '@mui/material';
import { 
	WarningAmberRounded, 
	ErrorOutlineRounded, 
	CheckCircleOutlineRounded,
	InfoOutlined
} from '@mui/icons-material';
import BaseDialog from './BaseDialog';
import type { ConfirmationDialogProps } from './types';

const ConfirmationDialog: React.FC<ConfirmationDialogProps> = ({
	open,
	onClose,
	onConfirm,
	title,
	subtitle,
	message,
	confirmLabel = 'Confirm',
	cancelLabel = 'Cancel',
	severity = 'warning',
	loading = false,
	maxWidth = 'xs',
	icon,
	children
}) => {
	const theme = useTheme();

	const getSeverityColor = () => {
		switch (severity) {
			case 'error': return theme.palette.error;
			case 'success': return theme.palette.success;
			case 'info': return theme.palette.info;
			case 'primary': return theme.palette.primary;
			default: return theme.palette.warning;
		}
	};

	const sevColor = getSeverityColor();

	const renderIcon = () => {
		if (icon) return icon;
		const iconStyle = { fontSize: 40, color: sevColor.main };
		switch (severity) {
			case 'error': return <ErrorOutlineRounded sx={iconStyle} />;
			case 'success': return <CheckCircleOutlineRounded sx={iconStyle} />;
			case 'info': return <InfoOutlined sx={iconStyle} />;
			default: return <WarningAmberRounded sx={iconStyle} />;
		}
	};

	const actions = (
		<>
			<Button 
				onClick={onClose} 
				disabled={loading}
				variant="text"
				sx={{ 
					color: 'text.secondary',
					textTransform: 'none',
					fontWeight: 600,
					px: 3,
					'&:hover': { bgcolor: alpha(theme.palette.secondary.main, 0.05) }
				}}
			>
				{cancelLabel}
			</Button>
			<Button
				variant="contained"
				onClick={onConfirm}
				disabled={loading}
				sx={{
					bgcolor: sevColor.main,
					color: 'white',
					textTransform: 'none',
					fontWeight: 700,
					px: 4,
					borderRadius: '4px',
					boxShadow: `0 4px 14px 0 ${alpha(sevColor.main, 0.39)}`,
					minWidth: 120,
					'&:hover': {
						bgcolor: sevColor.dark,
						boxShadow: `0 6px 20px 0 ${alpha(sevColor.main, 0.23)}`,
					}
				}}
			>
				{loading ? <CircularProgress size={20} color="inherit" /> : confirmLabel}
			</Button>
		</>
	);

	return (
		<BaseDialog
			open={open}
			onClose={onClose}
			title={title}
			subtitle={subtitle}
			maxWidth={maxWidth}
			loading={loading}
			actions={actions}
		>
			<Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: 2 }}>
				<Box sx={{ 
					p: 2, 
					borderRadius: '50%', 
					bgcolor: alpha(sevColor.main, 0.08),
					display: 'flex',
					mb: 1
				}}>
					{renderIcon()}
				</Box>
				<Typography variant="body1" sx={{ color: 'text.primary', fontWeight: 500, lineHeight: 1.6 }}>
					{message}
				</Typography>
				{children && (
					<Box sx={{ width: '100%', mt: 1 }}>
						{children}
					</Box>
				)}
			</Box>
		</BaseDialog>
	);
};

export default ConfirmationDialog;
