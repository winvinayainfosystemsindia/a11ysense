import React, { useState } from 'react';
import { Box, Paper, useTheme, Fade, Slide, alpha, Alert, Collapse } from '@mui/material';
import EnterpriseFormHeader, { type FormStep } from './EnterpriseFormHeader';
import EnterpriseFormFooter from './EnterpriseFormFooter';

interface EnterpriseFormProps {
	title: string;
	subtitle?: string;
	mode: 'create' | 'edit' | 'view';
	steps: FormStep[];
	onSave: () => void;
	onCancel: () => void;
	isSubmitting?: boolean;
	saveButtonText?: string;
	error?: string | null;
	onDelete?: () => void;
	headerActions?: React.ReactNode;
}

/**
 * EnterpriseForm Component.
 * A high-precision, multi-step layout for enterprise management consoles.
 * Synchronized with theme tokens for a professional "Enterprise Outcome".
 */
const EnterpriseForm: React.FC<EnterpriseFormProps> = ({
	title,
	subtitle,
	mode,
	steps,
	onSave,
	onCancel,
	isSubmitting = false,
	saveButtonText,
	error,
	onDelete,
	headerActions
}) => {
	const theme = useTheme();
	const [activeStep, setActiveStep] = useState(0);
	const [direction, setDirection] = useState<'left' | 'right'>('left');

	const handleNext = () => {
		if (activeStep < steps.length - 1) {
			setDirection('left');
			setActiveStep(prev => prev + 1);
		}
	};

	const handleBack = () => {
		if (activeStep > 0) {
			setDirection('right');
			setActiveStep(prev => prev - 1);
		}
	};

	const handleStepClick = (step: number) => {
		if (mode === 'view' || mode === 'edit' || step < activeStep) {
			setDirection(step > activeStep ? 'left' : 'right');
			setActiveStep(step);
		}
	};

	if (steps.length === 0) return null;

	return (
		<Paper elevation={0} sx={{
			display: 'flex',
			flexDirection: 'column',
			minHeight: { xs: 'calc(100vh - 100px)', md: '620px' },
			maxHeight: 'calc(100vh - 40px)',
			overflow: 'hidden',
			borderRadius: '4px',
			border: `1px solid ${theme.palette.divider}`,
			bgcolor: theme.palette.background.paper,
			boxShadow: theme.shadows[3],
			transition: 'all 0.2s ease-in-out'
		}}>
			<EnterpriseFormHeader
				title={title}
				subtitle={subtitle}
				mode={mode}
				activeStep={activeStep}
				steps={steps}
				onStepClick={handleStepClick}
				onClose={onCancel}
				headerActions={headerActions}
			/>

			<Box sx={{
				flex: 1,
				p: { xs: 3, md: 5, lg: 6 },
				overflowY: 'auto',
				overflowX: 'hidden',
				bgcolor: alpha(theme.palette.background.default, 0.4),
				position: 'relative'
			}}>
				{/* Step Content Container */}
				<Box sx={{ maxWidth: '1000px', mx: 'auto', position: 'relative' }}>
					<Collapse in={!!error}>
						{error && (
							<Alert 
								severity="error" 
								sx={{ 
									mb: 4, 
									borderRadius: '4px',
									border: `1px solid ${alpha(theme.palette.error.main, 0.2)}`,
									bgcolor: alpha(theme.palette.error.main, 0.02),
									'& .MuiAlert-message': { fontWeight: 600 }
								}}
							>
								{error}
							</Alert>
						)}
					</Collapse>
					{steps.map((step, index) => (
						index === activeStep && (
							<Fade in key={index} timeout={300}>
								<Slide direction={direction === 'left' ? 'left' : 'right'} in={index === activeStep} mountOnEnter unmountOnExit timeout={300}>
									<Box>
										{step.content}
									</Box>
								</Slide>
							</Fade>
						)
					))}
				</Box>
			</Box>

			<EnterpriseFormFooter
				activeStep={activeStep}
				totalSteps={steps.length}
				onBack={handleBack}
				onNext={handleNext}
				onSave={onSave}
				onCancel={onCancel}
				isSubmitting={isSubmitting}
				saveButtonText={saveButtonText}
				mode={mode}
				onDelete={onDelete}
			/>
		</Paper>
	);
};

export default EnterpriseForm;
export { type FormStep };
