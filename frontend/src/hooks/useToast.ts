import { useSnackbar, type VariantType } from 'notistack';
import { useCallback, useMemo } from 'react';

const useToast = () => {
	const { enqueueSnackbar } = useSnackbar();

	const showToast = useCallback((message: string, variant: VariantType = 'default') => {
		enqueueSnackbar(message, {
			variant,
			autoHideDuration: 3000,
			anchorOrigin: {
				vertical: 'bottom',
				horizontal: 'right',
			}
		});
	}, [enqueueSnackbar]);

	return useMemo(() => ({
		showToast,
		success: (message: string) => showToast(message, 'success'),
		error: (message: string) => showToast(message, 'error'),
		info: (message: string) => showToast(message, 'info'),
		warning: (message: string) => showToast(message, 'warning'),
	}), [showToast]);
};

export default useToast;
