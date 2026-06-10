import React from 'react';
import { useNavigate } from '@tanstack/react-router';
import {
	Container,
	Typography,
	Button,
	useTheme,
} from '@mui/material';
import { ErrorOutlined as ErrorIcon } from '@mui/icons-material';

const NotFoundPage: React.FC = () => {
	const theme = useTheme();
	const navigate = useNavigate();

	return (
		<Container component="main" maxWidth="md" sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '80vh' }}>
			<ErrorIcon color="error" sx={{ fontSize: 100, mb: 2, opacity: 0.5 }} aria-hidden="true" />

			<Typography variant="h1" component="div" gutterBottom sx={{ fontWeight: 900, color: theme.palette.text.secondary }}>
				404
			</Typography>

			<Typography variant="h4" component="h1" gutterBottom align="center" sx={{ fontWeight: 700 }}>
				Page Not Found
			</Typography>

			<Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 5, maxWidth: 500 }}>
				Oops! The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.
			</Typography>

			<Button
				variant="contained"
				size="large"
				onClick={() => {
					const orgId = localStorage.getItem('org_id');
					if (orgId) {
						navigate({ to: '/org/$orgId/dashboard', params: { orgId } });
					} else {
						navigate({ to: '/auth/signin' });
					}
				}}
				sx={{
					px: 4,
					py: 1.5,
					borderRadius: '10px', // Matches custom theme button overrides
				}}
			>
				Back to Dashboard
			</Button>
		</Container>
	);
};

export default NotFoundPage;
