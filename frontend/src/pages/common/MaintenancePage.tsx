import React from 'react';
import {
	Container,
	Typography,
	Paper,
	useTheme,
} from '@mui/material';
import { BuildCircle as BuildIcon } from '@mui/icons-material';

const MaintenancePage: React.FC = () => {
	const theme = useTheme();

	return (
		<Container component="main" maxWidth="sm" sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
			<Paper
				elevation={0}
				sx={{
					p: 6,
					display: 'flex',
					flexDirection: 'column',
					alignItems: 'center',
					border: `1px solid ${theme.palette.divider}`,
					borderRadius: '16px', // Matches custom theme card overrides
					backgroundColor: theme.palette.background.paper,
				}}
			>
				<BuildIcon color="warning" sx={{ fontSize: 80, mb: 3 }} aria-hidden="true" />

				<Typography variant="h4" component="h1" gutterBottom align="center" sx={{ fontWeight: 700 }}>
					Under Maintenance
				</Typography>

				<Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 3 }}>
					We apologize for the inconvenience. We are currently performing scheduled maintenance to improve our services and auditing metrics.
				</Typography>

				<Typography variant="body2" color="text.disabled" align="center" sx={{ fontWeight: 600 }}>
					Please check back soon.
				</Typography>
			</Paper>
		</Container>
	);
};

export default MaintenancePage;
