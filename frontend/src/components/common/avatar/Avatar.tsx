import React from 'react';
import { Avatar as MuiAvatar, type AvatarProps as MuiAvatarProps, useTheme } from '@mui/material';

export interface EnterpriseAvatarProps extends MuiAvatarProps {
	name: string;
	size?: number;
}

/**
 * EnterpriseAvatar Component
 * A professional, character-based avatar that generates consistent colors from names.
 * Optimized for enterprise consoles with a clean, semi-square aesthetic.
 */
const EnterpriseAvatar: React.FC<EnterpriseAvatarProps> = ({ name, size = 40, sx, ...props }) => {
	const theme = useTheme();

	// Enterprise color palette (consistent with AWS/Cloudscape outcomes)
	const colors = [
		theme.palette.primary.main,
		theme.palette.secondary.main,
		'#ec7211', // AWS Orange
		'#232f3e', // AWS Dark Blue
		'#007eb9', // AWS Blue
		'#1d8102', // AWS Green
		'#d13212', // AWS Red
		'#ff9900', // Amazon Orange
		'#545b64', // AWS Gray
	];

	const stringToColor = (str: string) => {
		let hash = 0;
		for (let i = 0; i < str.length; i++) {
			hash = str.charCodeAt(i) + ((hash << 5) - hash);
		}
		const index = Math.abs(hash) % colors.length;
		return colors[index];
	};

	const getInitials = (str: string) => {
		if (!str) return '';
		return str
			.split(' ')
			.map((n) => n[0])
			.slice(0, 2)
			.join('')
			.toUpperCase();
	};

	const color = stringToColor(name);
	
	return (
		<MuiAvatar
			{...props}
			sx={{
				bgcolor: color,
				width: size,
				height: size,
				fontSize: `${size * 0.4}px`,
				fontWeight: 700,
				borderRadius: '4px', // Enterprise precision
				border: `1px solid ${theme.palette.divider}`,
				...sx
			}}
		>
			{getInitials(name)}
		</MuiAvatar>
	);
};

export default EnterpriseAvatar;
