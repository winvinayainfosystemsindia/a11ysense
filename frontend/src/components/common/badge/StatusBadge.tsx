import React from 'react';
import { Box, Typography } from '@mui/material';
import { useTheme, alpha } from '@mui/material/styles';

export type BadgeType = 'lead' | 'deal' | 'task' | 'company' | 'generic';

interface StatusBadgeProps {
	label: string;
	status: string;
	type?: BadgeType;
}

type StatusTone = 'success' | 'info' | 'warning' | 'error' | 'default';

const getStatusTone = (status: string, type: BadgeType): StatusTone => {
	const s = status.toLowerCase();

	if (type === 'lead') {
		if (['qualified', 'converted'].includes(s)) return 'success';
		if (['contacted', 'negotiation', 'proposal_sent'].includes(s)) return 'info';
		if (['new', 'nurturing'].includes(s)) return 'warning';
		if (['lost'].includes(s)) return 'error';
	}

	if (type === 'deal') {
		if (['closed_won'].includes(s)) return 'success';
		if (['proposal', 'negotiation', 'discovery', 'qualification'].includes(s)) return 'info';
		if (['on_hold'].includes(s)) return 'warning';
		if (['closed_lost'].includes(s)) return 'error';
	}

	if (type === 'task') {
		if (['completed'].includes(s)) return 'success';
		if (['in_progress'].includes(s)) return 'info';
		if (['pending', 'deferred'].includes(s)) return 'warning';
		if (['cancelled'].includes(s)) return 'error';
	}

	// Company & generic
	if (['active', 'client', 'customer', 'partner'].includes(s)) return 'success';
	if (['prospect'].includes(s)) return 'info';
	if (['inactive'].includes(s)) return 'error';

	return 'default';
};

const StatusBadge: React.FC<StatusBadgeProps> = ({ label, status, type = 'generic' }) => {
	const theme = useTheme();
	const tone = getStatusTone(status, type);

	const paletteColor = {
		success: theme.palette.success.main,
		info:    theme.palette.primary.main,
		warning: theme.palette.warning.main,
		error:   theme.palette.error.main,
		default: theme.palette.text.disabled,
	}[tone];

	return (
		<Box
			sx={{
				display: 'inline-flex',
				alignItems: 'center',
				gap: 0.75,
				px: 1.25,
				py: 0.4,
				borderRadius: '6px',
				bgcolor: alpha(paletteColor, 0.1),
				border: `1px solid ${alpha(paletteColor, 0.25)}`,
			}}
		>
			{/* Status dot */}
			<Box
				sx={{
					width: 6,
					height: 6,
					borderRadius: '50%',
					bgcolor: paletteColor,
					flexShrink: 0,
				}}
			/>
			<Typography
				variant="caption"
				sx={{
					fontWeight: 600,
					textTransform: 'capitalize',
					fontSize: '0.72rem',
					letterSpacing: '0.02em',
					color: paletteColor,
					lineHeight: 1,
				}}
			>
				{label}
			</Typography>
		</Box>
	);
};

export default StatusBadge;
