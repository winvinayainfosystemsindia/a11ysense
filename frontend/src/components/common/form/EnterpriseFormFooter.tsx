import React from 'react';
import {
	Box,
	Button,
	Typography,
	useTheme,
	alpha,
	CircularProgress
} from '@mui/material';
import { NavigateBefore, NavigateNext, Save, Delete as DeleteIcon } from '@mui/icons-material';

interface EnterpriseFormFooterProps {
	activeStep: number;
	totalSteps: number;
	onBack: () => void;
	onNext: () => void;
	onSave: () => void;
	onCancel: () => void;
	isSubmitting?: boolean;
	saveDisabled?: boolean;
	useAccent?: boolean;
	saveButtonText?: string;
	mode: 'create' | 'edit' | 'view';
	onDelete?: () => void;
}

/**
 * Standard Footer for EnterpriseForm.
 * Features theme-synced navigation and professional console interactions.
 */
const EnterpriseFormFooter: React.FC<EnterpriseFormFooterProps> = ({
	activeStep,
	totalSteps,
	onBack,
	onNext,
	onSave,
	onCancel,
	isSubmitting = false,
	saveDisabled = false,
	useAccent = true,
	saveButtonText = 'Save Changes',
	mode,
	onDelete
}) => {
	const theme = useTheme();
	const isLastStep = activeStep === totalSteps - 1;

	const accentColor = useAccent 
		? ((theme.palette as any).accent?.main || theme.palette.primary.main)
		: theme.palette.primary.main;
		
	const accentDark = useAccent
		? ((theme.palette as any).accent?.dark || theme.palette.primary.dark)
		: theme.palette.primary.dark;

	return (
		<Box sx={{
			p: { xs: 2, md: 2.5 },
			px: { xs: 3, md: 4 },
			borderTop: `1px solid ${theme.palette.divider}`,
			bgcolor: alpha(theme.palette.background.paper, 0.95),
			backdropFilter: 'blur(8px)',
			display: 'flex',
			justifyContent: 'space-between',
			alignItems: 'center',
			position: 'sticky',
			bottom: 0,
			zIndex: 10
		}}>
			<Box sx={{ display: 'flex', gap: 1.5 }}>
				<Button
					variant="outlined"
					onClick={onCancel}
					sx={{
						textTransform: 'none',
						fontWeight: 600,
						px: 3,
						color: theme.palette.text.secondary,
						borderColor: theme.palette.divider,
						borderRadius: '4px',
						'&:hover': {
							borderColor: theme.palette.text.primary,
							bgcolor: alpha(theme.palette.text.primary, 0.05)
						}
					}}
				>
					{mode === 'view' ? 'Close' : 'Cancel'}
				</Button>

				{mode === 'edit' && onDelete && (
					<Button
						variant="outlined"
						color="error"
						startIcon={<DeleteIcon />}
						onClick={onDelete}
						sx={{
							textTransform: 'none',
							fontWeight: 600,
							px: 2,
							borderRadius: '4px',
							borderColor: alpha(theme.palette.error.main, 0.3),
							'&:hover': {
								borderColor: theme.palette.error.main,
								bgcolor: alpha(theme.palette.error.main, 0.05)
							}
						}}
					>
						Delete
					</Button>
				)}
			</Box>

			<Box sx={{ display: 'flex', gap: 3, alignItems: 'center' }}>
				{totalSteps > 1 && (
					<Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700, letterSpacing: '0.02em' }}>
						STEP {activeStep + 1} OF {totalSteps}
					</Typography>
				)}

				<Box sx={{ display: 'flex', gap: 1.5 }}>
					{activeStep > 0 && (
						<Button
							variant="outlined"
							startIcon={<NavigateBefore />}
							onClick={onBack}
							sx={{
								textTransform: 'none',
								fontWeight: 600,
								borderRadius: '4px',
								px: 2,
								color: theme.palette.text.primary,
								borderColor: theme.palette.divider
							}}
						>
							Back
						</Button>
					)}

					{mode !== 'view' && (
						isLastStep ? (
							<Button
								variant="contained"
								startIcon={isSubmitting ? <CircularProgress size={16} color="inherit" /> : <Save />}
								onClick={onSave}
								disabled={isSubmitting || saveDisabled}
								sx={{
									textTransform: 'none',
									fontWeight: 700,
									borderRadius: '4px',
									px: 4,
									bgcolor: accentColor,
									boxShadow: 'none',
									'&:hover': {
										bgcolor: accentDark,
										boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
									},
									'&.Mui-disabled': {
										bgcolor: alpha(accentColor, 0.3),
										color: alpha('#fff', 0.8)
									}
								}}
							>
								{isSubmitting ? 'Saving...' : (mode === 'create' ? 'Create' : saveButtonText)}
							</Button>
						) : (
							<Button
								variant="contained"
								endIcon={isSubmitting ? <CircularProgress size={16} color="inherit" /> : <NavigateNext />}
								onClick={onNext}
								disabled={isSubmitting || saveDisabled}
								sx={{
									textTransform: 'none',
									fontWeight: 700,
									borderRadius: '4px',
									px: 3,
									bgcolor: theme.palette.primary.main,
									boxShadow: 'none',
									'&:hover': {
										bgcolor: theme.palette.primary.dark,
										boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
									},
									'&.Mui-disabled': {
										bgcolor: alpha(theme.palette.primary.main, 0.3),
										color: alpha('#fff', 0.8)
									}
								}}
							>
								{isSubmitting ? 'Processing...' : 'Next Step'}
							</Button>
						)
					)}
				</Box>
			</Box>
		</Box>
	);
};

export default EnterpriseFormFooter;
