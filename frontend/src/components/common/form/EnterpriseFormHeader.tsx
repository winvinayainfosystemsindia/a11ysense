import React from 'react';
import {
	Box,
	Typography,
	Stepper,
	Step,
	StepLabel,
	Chip,
	useTheme,
	alpha,
	LinearProgress,
	IconButton,
	type StepIconProps
} from '@mui/material';
import { Check, Close as CloseIcon } from '@mui/icons-material';

export interface FormStep {
	label: string;
	description?: string;
	content: React.ReactNode;
}

interface EnterpriseFormHeaderProps {
	title: string;
	subtitle?: string;
	mode: 'create' | 'edit' | 'view';
	activeStep: number;
	steps: FormStep[];
	onStepClick?: (step: number) => void;
	onClose?: () => void;
	headerActions?: React.ReactNode;
}

/**
 * Custom Step Icon for a high-precision Enterprise Console.
 * Sized and styled to match AWS-style compactness.
 */
const ConsoleStepIcon = (props: StepIconProps) => {
	const { active, completed, icon, error } = props;
	const theme = useTheme();

	return (
		<Box
			sx={{
				width: 24,
				height: 24,
				borderRadius: '50%',
				display: 'flex',
				alignItems: 'center',
				justifyContent: 'center',
				bgcolor: error
					? theme.palette.error.main
					: completed
						? theme.palette.success.main
						: active
							? theme.palette.primary.main
							: alpha(theme.palette.text.disabled, 0.1),
				color: completed || active || error ? '#fff' : theme.palette.text.secondary,
				fontWeight: 700,
				fontSize: '0.75rem',
				transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
				zIndex: 1
			}}
		>
			{completed ? (
				<Check sx={{ fontSize: 14 }} />
			) : (
				icon
			)}
		</Box>
	);
};

/**
 * High-precision Header for Enterprise Console Forms.
 * Integrated close icon and streamlined progress navigation.
 */
const EnterpriseFormHeader: React.FC<EnterpriseFormHeaderProps> = ({
	title,
	subtitle,
	mode,
	activeStep,
	steps,
	onStepClick,
	onClose,
	headerActions
}) => {
	const theme = useTheme();
	const progress = ((activeStep + 1) / steps.length) * 100;

	const getModeConfig = () => {
		switch (mode) {
			case 'view':
				return { label: 'READ ONLY', color: theme.palette.text.secondary, bgcolor: alpha(theme.palette.text.secondary, 0.1) };
			case 'edit':
				return { label: 'EDITING', color: theme.palette.warning.dark, bgcolor: alpha(theme.palette.warning.main, 0.1) };
			default:
				return { label: 'NEW', color: theme.palette.primary.main, bgcolor: alpha(theme.palette.primary.main, 0.1) };
		}
	};

	const modeConfig = getModeConfig();

	return (
		<Box sx={{
			position: 'relative',
			borderBottom: `1px solid ${theme.palette.divider}`,
			bgcolor: theme.palette.background.paper
		}}>
			{/* Precise 2px Brand Accent */}
			<Box sx={{
				position: 'absolute',
				top: 0,
				left: 0,
				right: 0,
				height: 2,
				bgcolor: theme.palette.primary.main
			}} />

			<Box sx={{ p: { xs: 2.5, md: 3 }, pb: 2 }}>
				<Box sx={{
					display: 'flex',
					justifyContent: 'space-between',
					alignItems: 'flex-start',
					mb: 3
				}}>
					<Box sx={{ pr: 6 }}>
						<Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 0.5, flexWrap: 'wrap' }}>
							<Typography variant="h6" sx={{ fontWeight: 800, color: theme.palette.text.primary, fontSize: '1.1rem', letterSpacing: '-0.01em' }}>
								{title}
							</Typography>
							<Chip
								label={modeConfig.label}
								size="small"
								sx={{
									bgcolor: modeConfig.bgcolor,
									color: modeConfig.color,
									fontWeight: 800,
									fontSize: '0.6rem',
									height: 18,
									borderRadius: '4px',
									letterSpacing: '0.02em'
								}}
							/>
						</Box>
						{subtitle && (
							<Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem', fontWeight: 500, lineHeight: 1.4 }}>
								{subtitle}
							</Typography>
						)}
					</Box>
					{onClose && (
						<Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: -0.5, mr: -0.5 }}>
							{headerActions}
							<IconButton
								onClick={onClose}
								size="small"
								sx={{
									color: theme.palette.text.secondary,
									'&:hover': { color: theme.palette.error.main, bgcolor: alpha(theme.palette.error.main, 0.05) }
								}}
							>
								<CloseIcon fontSize="small" />
							</IconButton>
						</Box>
					)}
				</Box>

				<Box sx={{
					width: '100%',
					overflowX: 'auto',
					WebkitOverflowScrolling: 'touch',
					pb: { xs: 1.5, md: 0 },
					'&::-webkit-scrollbar': { height: 4 },
					'&::-webkit-scrollbar-thumb': { bgcolor: alpha(theme.palette.text.disabled, 0.2), borderRadius: 2 }
				}}>
					<Stepper
						activeStep={activeStep}
						sx={{
							minWidth: { xs: 500, md: 'auto' },
							px: 0,
							'& .MuiStepLabel-label': {
								fontSize: '0.75rem',
								fontWeight: 600,
								pt: 0.5,
								color: theme.palette.text.disabled,
								'&.Mui-active': { color: theme.palette.primary.main, fontWeight: 800 },
								'&.Mui-completed': { color: theme.palette.text.primary, fontWeight: 700 }
							},
							'& .MuiStepConnector-root': { top: 12 },
							'& .MuiStepConnector-line': { borderColor: theme.palette.divider, borderTopWidth: 1 }
						}}
					>
						{steps.map((step, index) => (
							<Step key={step.label} onClick={onStepClick ? () => onStepClick(index) : undefined} sx={{ cursor: onStepClick ? 'pointer' : 'default' }}>
								<StepLabel 
									slots={{ stepIcon: ConsoleStepIcon }}
									optional={step.description && (
										<Typography variant="caption" sx={{ fontSize: '0.65rem', display: { xs: 'none', md: 'block' }, opacity: 0.8 }}>
											{step.description}
										</Typography>
									)}
								>
									{step.label}
								</StepLabel>
							</Step>
						))}
					</Stepper>
				</Box>
			</Box>

			{/* Subtle Integrated Linear Progress */}
			<LinearProgress
				variant="determinate"
				value={progress}
				sx={{
					height: 2,
					bgcolor: 'transparent',
					'& .MuiLinearProgress-bar': { transition: 'transform 0.4s cubic-bezier(0.4, 0, 0.2, 1)' }
				}}
			/>
		</Box>
	);
};

export default EnterpriseFormHeader;
