import React from 'react';
import { Breadcrumbs as MuiBreadcrumbs, Link, Typography, Box, alpha, useTheme } from '@mui/material';
import { Link as RouterLink, useLocation } from '@tanstack/react-router';
import {
	NavigateNext as NavigateNextIcon,
	Home as HomeIcon,
	Dashboard as DashboardIcon,
	FactCheck as AuditIcon,
	LockOpen as LoginIcon,
	PersonAdd as RegisterIcon
} from '@mui/icons-material';

const breadcrumbNameMap: { [key: string]: { name: string; icon?: React.ReactNode } } = {
	'dashboard': { name: 'Dashboard', icon: <DashboardIcon sx={{ fontSize: 'inherit' }} /> },
	'audit': { name: 'Auditing & Compliance', icon: <AuditIcon sx={{ fontSize: 'inherit' }} /> },
	'login': { name: 'Login', icon: <LoginIcon sx={{ fontSize: 'inherit' }} /> },
	'register': { name: 'Register', icon: <RegisterIcon sx={{ fontSize: 'inherit' }} /> }
};

const Breadcrumbs: React.FC = () => {
	const theme = useTheme();
	const location = useLocation();
	const pathnames = location.pathname.split('/').filter((x) => x);

	if (pathnames.length === 0) {
		return null;
	}

	return (
		<Box sx={{ mb: 3, mt: 1 }}>
			<MuiBreadcrumbs
				separator={
					<NavigateNextIcon 
						sx={{ 
							fontSize: '1rem', 
							color: alpha(theme.palette.text.secondary, 0.4) 
						}} 
					/>
				}
				aria-label="breadcrumb"
				sx={{
					'& .MuiBreadcrumbs-ol': { alignItems: 'center' }
				}}
			>
				{/* Root Navigation */}
				<Link
					component={RouterLink}
					underline="hover"
					to="/dashboard"
					sx={{
						display: 'flex',
						alignItems: 'center',
						gap: 0.75,
						color: theme.palette.text.secondary,
						fontSize: '0.875rem',
						fontWeight: 500,
						transition: theme.transitions.create(['color']),
						'&:hover': { 
							color: theme.palette.primary.main,
						}
					}}
				>
					<HomeIcon sx={{ fontSize: '1.1rem', color: alpha(theme.palette.text.secondary, 0.6) }} />
					Home
				</Link>

				{pathnames.map((value, index) => {
					const last = index === pathnames.length - 1;
					const to = `/${pathnames.slice(0, index + 1).join('/')}`;

					const breadcrumbInfo = breadcrumbNameMap[value];
					const name = breadcrumbInfo?.name || value.charAt(0).toUpperCase() + value.slice(1).replace(/-/g, ' ');
					const icon = breadcrumbInfo?.icon;

					if (value === 'dashboard') {
						return null;
					}

					return last ? (
						<Typography
							key={to}
							variant="body2"
							sx={{
								display: 'flex',
								alignItems: 'center',
								gap: 0.75,
								color: theme.palette.text.primary,
								fontWeight: 700,
								fontSize: '0.875rem'
							}}
						>
							{icon && (
								<Box sx={{ display: 'flex', color: alpha(theme.palette.text.secondary, 0.6) }}>
									{icon}
								</Box>
							)}
							{name}
						</Typography>
					) : (
						<Link
							component={RouterLink}
							underline="hover"
							to={to as any}
							key={to}
							sx={{
								display: 'flex',
								alignItems: 'center',
								gap: 0.75,
								color: theme.palette.text.secondary,
								fontSize: '0.875rem',
								fontWeight: 500,
								transition: theme.transitions.create(['color']),
								'&:hover': { 
									color: theme.palette.primary.main,
								}
							}}
						>
							{icon && (
								<Box sx={{ display: 'flex', color: alpha(theme.palette.text.secondary, 0.6) }}>
									{icon}
								</Box>
							)}
							{name}
						</Link>
					);
				})}
			</MuiBreadcrumbs>
		</Box>
	);
};

export default Breadcrumbs;
