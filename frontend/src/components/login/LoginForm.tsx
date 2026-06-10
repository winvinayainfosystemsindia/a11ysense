import { 
  Box, 
  TextField, 
  Stack, 
  InputAdornment, 
  IconButton, 
  Checkbox, 
  FormControlLabel, 
  Typography, 
  CircularProgress,
  Link as MuiLink 
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { Link } from '@tanstack/react-router';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { Button } from '../common/button';
import DemoAccounts from './DemoAccounts';

interface LoginFormProps {
  email: string;
  setEmail: (val: string) => void;
  password: string;
  setPassword: (val: string) => void;
  showPassword: boolean;
  setShowPassword: (val: boolean) => void;
  loading: boolean;
  onSubmit: (e: React.FormEvent) => void;
  onPrefill: (role: 'admin' | 'auditor') => void;
}

const LoginForm: React.FC<LoginFormProps> = ({
  email,
  setEmail,
  password,
  setPassword,
  showPassword,
  setShowPassword,
  loading,
  onSubmit,
  onPrefill
}) => {
  return (
    <form onSubmit={onSubmit}>
      <Stack spacing={1.75}>

        {/* Email Field with label outside */}
        <Box>
          <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5, color: 'text.primary', display: 'block', textAlign: 'left', fontSize: '0.8rem' }}>
            Email Address
          </Typography>
          <TextField
            fullWidth
            placeholder="name@company.com"
            variant="outlined"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            slotProps={{
              input: {
                sx: { 
                  height: '40px',
                  fontSize: '0.85rem',
                  borderRadius: '8px', 
                  backgroundColor: 'background.paper',
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'divider'
                  },
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'text.disabled'
                  },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'primary.main'
                  }
                }
              }
            }}
            disabled={loading}
          />
        </Box>

        {/* Password Field with label outside and Inline Forgot Password */}
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
            <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.primary', fontSize: '0.8rem' }}>
              Password
            </Typography>
            <MuiLink href="#" sx={{ fontSize: '0.75rem', fontWeight: 600, color: 'primary.main', textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}>
              Forgot password?
            </MuiLink>
          </Box>
          <TextField
            fullWidth
            placeholder="••••••••"
            variant="outlined"
            type={showPassword ? 'text' : 'password'}
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            slotProps={{
              input: {
                sx: { 
                  height: '40px',
                  fontSize: '0.85rem',
                  borderRadius: '8px', 
                  backgroundColor: 'background.paper',
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'divider'
                  },
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'text.disabled'
                  },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'primary.main'
                  }
                },
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={() => setShowPassword(!showPassword)} edge="end" size="small">
                      {showPassword ? <VisibilityOff sx={{ fontSize: 18 }} /> : <Visibility sx={{ fontSize: 18 }} />}
                    </IconButton>
                  </InputAdornment>
                )
              }
            }}
            disabled={loading}
          />
        </Box>

        {/* Keep me signed in Checkbox */}
        <FormControlLabel 
          control={
            <Checkbox 
              defaultChecked 
              sx={{ 
                color: 'text.disabled', 
                '&.Mui-checked': { color: 'primary.main' },
                p: 0.25
              }} 
            />
          } 
          label={
            <Typography variant="body2" sx={{ color: 'text.secondary', fontWeight: 500, userSelect: 'none', ml: 0.25, fontSize: '0.775rem' }}>
              Keep me signed in for 30 days
            </Typography>
          } 
          sx={{ width: 'fit-content', m: 0 }}
        />

        {/* Sign In Button with endIcon */}
        <Button
          type="submit"
          variant="contained"
          size="medium"
          fullWidth
          endIcon={<ArrowForwardIcon sx={{ fontSize: '1rem !important' }} />}
          sx={{ 
            py: 1, 
            borderRadius: '8px', 
            fontWeight: '600',
            fontSize: '0.85rem',
            textTransform: 'none',
            bgcolor: 'primary.main',
            '&:hover': {
              bgcolor: 'primary.dark',
            }
          }}
          disabled={loading}
        >
          {loading ? <CircularProgress size={20} color="inherit" /> : 'Sign In'}
        </Button>

        {/* Developer Demo Access panel (Clean integration) */}
        <DemoAccounts onPrefill={onPrefill} />

        {/* New to A11ySense AI Divider */}
        <Box sx={{ display: 'flex', alignItems: 'center', my: 0.5 }}>
          <Box sx={{ flexGrow: 1, height: '1px', bgcolor: 'divider' }} />
          <Typography variant="body2" sx={{ px: 1.5, color: 'text.secondary', fontWeight: 500, fontSize: '0.75rem' }}>
            New to A11ySense AI?
          </Typography>
          <Box sx={{ flexGrow: 1, height: '1px', bgcolor: 'divider' }} />
        </Box>

        {/* Create Account redirect button */}
        <Link to="/auth/signup" style={{ textDecoration: 'none', width: '100%', display: 'block' }}>
          <Button
            variant="outlined"
            fullWidth
            sx={{
              py: 0.85,
              borderRadius: '8px',
              fontWeight: '600',
              fontSize: '0.85rem',
              textTransform: 'none',
              color: 'primary.main',
              borderColor: 'primary.main',
              '&:hover': {
                borderColor: 'primary.dark',
                backgroundColor: (theme) => alpha(theme.palette.primary.main, 0.04),
              }
            }}
          >
            Create an Account
          </Button>
        </Link>

      </Stack>
    </form>
  );
};

export default LoginForm;
