import React from 'react';
import { Box, Typography, SvgIcon, alpha, useTheme } from '@mui/material';
import type { SvgIconComponent } from '@mui/icons-material';
import type { SxProps, Theme } from '@mui/material';

export interface StatCardProps {
	title?: string;
	label?: string; // Alias for title
	value?: React.ReactNode;
	count?: React.ReactNode; // Alias for value
	unit?: string;
	subtitle?: string; // Descriptive text at the bottom
	icon?: React.ReactNode | SvgIconComponent;
	color?: string; // Accent color
	children?: React.ReactNode;
	sx?: SxProps<Theme>;
}

const getThemeColor = (theme: Theme, colorPath?: string): string => {
	if (!colorPath) return theme.palette.primary.main;
	const parts = colorPath.split('.');
	let current: any = theme.palette;
	for (const part of parts) {
		if (current && part in current) {
			current = current[part];
		} else {
			return colorPath;
		}
	}
	return typeof current === 'string' ? current : colorPath;
};

const StatCard: React.FC<StatCardProps> = ({ 
	title, 
	label, 
	value: propValue, 
	count, 
	unit, 
	subtitle,
	icon, 
	children,
	color, 
	sx 
}) => {
	const theme = useTheme();
	const finalTitle = title || label;
	const finalValue = propValue !== undefined ? propValue : count;
	const activeColor = getThemeColor(theme, color);

	return (
		<Box
			sx={{
				p: 2.5,
				bgcolor: theme.palette.background.paper,
				borderRadius: '16px', // Matches custom theme card overrides
				border: `1px solid ${theme.palette.divider}`,
				boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.02), 0 1px 2px -1px rgba(0, 0, 0, 0.02)',
				display: 'flex',
				flexDirection: 'column',
				gap: 1.5,
				transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
				'&:hover': {
					transform: 'translateY(-2px)',
					boxShadow: '0 10px 15px -3px rgba(148, 163, 184, 0.08), 0 4px 6px -4px rgba(148, 163, 184, 0.08)',
				},
				height: '100%',
				...sx
			}}
		>
			{/* Top: Icon + Title */}
			<Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
				{icon && (
					<Box 
						sx={{ 
							display: 'flex', 
							alignItems: 'center', 
							justifyContent: 'center',
							width: 32,
							height: 32,
							borderRadius: '8px',
							bgcolor: alpha(activeColor, 0.1),
							color: activeColor
						}}
					>
						{React.isValidElement(icon) ? 
							React.cloneElement(icon as React.ReactElement<any>, { 
								sx: { fontSize: '1.2rem' } 
							}) : 
							<SvgIcon component={icon as any} sx={{ fontSize: '1.2rem' }} />
						}
					</Box>
				)}
				<Typography 
					variant="caption" 
					sx={{ 
						color: theme.palette.text.secondary, 
						fontWeight: 700, 
						textTransform: 'uppercase', 
						letterSpacing: '0.025em', 
						fontSize: '0.7rem' 
					}}
				>
					{finalTitle}
				</Typography>
			</Box>

			{/* Middle: Value + Unit */}
			<Box sx={{ mt: 'auto' }}>
				<Box sx={{ display: 'flex', alignItems: 'baseline', gap: 0.5 }}>
					<Typography 
						variant="h4" 
						sx={{ 
							fontWeight: 700, 
							color: theme.palette.text.primary,
							lineHeight: 1
						}}
					>
						{finalValue}
					</Typography>
					{unit && (
						<Typography 
							variant="subtitle2" 
							sx={{ 
								color: theme.palette.text.secondary, 
								fontWeight: 600 
							}}
						>
							{unit}
						</Typography>
					)}
				</Box>

				{/* Bottom: Subtitle or Children */}
				{subtitle && !children && (
					<Typography 
						variant="caption" 
						sx={{ 
							color: theme.palette.text.disabled, 
							fontWeight: 500,
							mt: 0.5,
							display: 'block'
						}}
					>
						{subtitle}
					</Typography>
				)}
				{children && (
					<Box sx={{ mt: 0.5 }}>
						{children}
					</Box>
				)}
			</Box>
		</Box>
	);
};

export default StatCard;
