import React from 'react';
import { useSearch, useNavigate } from '@tanstack/react-router';
import {
	Container,
	Paper,
	Typography,
	Button,
	useTheme,
} from '@mui/material';
import { CheckCircleOutlined as CheckCircleIcon } from '@mui/icons-material';

const SuccessPage: React.FC = () => {
	const theme = useTheme();
	const navigate = useNavigate();
	const search = useSearch({ strict: false }) as any;

	const title = search.title || 'Submission Successful';
	const message = search.message || 'Your information has been successfully submitted.';
	const actionText = search.actionText || 'Back to Dashboard';
	let actionPath = search.actionPath || '/dashboard';
	if (actionPath === '/dashboard') {
		const orgId = localStorage.getItem('org_id');
		if (orgId) {
			actionPath = `/org/${orgId}/dashboard`;
		}
	}

	return (
		<Container component="main" maxWidth="sm" sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '80vh' }}>
			<Paper
				elevation={0}
				sx={{
					p: 6,
					display: 'flex',
					flexDirection: 'column',
					alignItems: 'center',
					border: `1px solid ${theme.palette.divider}`,
					borderRadius: '16px', // Matches custom theme card overrides
					bgcolor: theme.palette.background.paper
				}}
			>
				<CheckCircleIcon color="success" sx={{ fontSize: 80, mb: 3 }} aria-hidden="true" />

				<Typography variant="h4" component="h1" gutterBottom align="center" sx={{ fontWeight: 700 }}>
					{title}
				</Typography>

				<Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 4, whiteSpace: 'pre-line' }}>
					{message}
				</Typography>

				<Button
					variant="contained"
					size="large"
					onClick={() => navigate({ to: actionPath as any })}
					sx={{
						px: 4,
						py: 1.5,
						borderRadius: '10px', // Matches custom theme overrides
					}}
				>
					{actionText}
				</Button>
			</Paper>
		</Container>
	);
};

export default SuccessPage;
