import React from 'react';
import { 
  Box, 
  TextField, 
  Paper, 
  CircularProgress, 
  Alert, 
  Stack, 
  InputAdornment, 
  IconButton, 
  MenuItem, 
  Checkbox,
  FormControlLabel,
  Typography,
  Link as MuiLink 
} from '@mui/material';
import EmailIcon from '@mui/icons-material/Email';
import LockIcon from '@mui/icons-material/Lock';
import CorporateFareIcon from '@mui/icons-material/CorporateFare';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import BadgeIcon from '@mui/icons-material/Badge';
import PersonIcon from '@mui/icons-material/Person';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { Button } from '../common/button';

interface RegisterFormProps {
  fullName: string;
  setFullName: (val: string) => void;
  email: string;
  setEmail: (val: string) => void;
  orgName: string;
  setOrgName: (val: string) => void;
  role: string;
  setRole: (val: string) => void;
  password: string;
  setPassword: (val: string) => void;
  showPassword: boolean;
  setShowPassword: (val: boolean) => void;
  agree: boolean;
  setAgree: (val: boolean) => void;
  loading: boolean;
  success: boolean;
  onSubmit: (e: React.FormEvent) => void;
}

const RegisterForm: React.FC<RegisterFormProps> = ({
  fullName,
  setFullName,
  email,
  setEmail,
  orgName,
  setOrgName,
  role,
  setRole,
  password,
  setPassword,
  showPassword,
  setShowPassword,
  agree,
  setAgree,
  loading,
  success,
  onSubmit
}) => {
  return (
    <Paper elevation={0} sx={{ 
      p: { xs: 2.5, sm: 3 }, 
      borderRadius: '16px', 
      borderColor: 'divider',
      backgroundColor: 'background.paper'
    }}>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: '700', color: 'text.primary', fontSize: '1.1rem' }}>
          Create your account
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.25, fontSize: '0.8rem' }}>
          Start auditing with enterprise-grade precision today.
        </Typography>
      </Box>

      <form onSubmit={onSubmit}>
        <Stack spacing={1.5}>
          {success && (
            <Alert severity="success" sx={{ borderRadius: '8px', py: 0.25, px: 1.5, fontSize: '0.75rem' }}>
              Registration successful! Redirecting to sign in...
            </Alert>
          )}

          {/* Full Name */}
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5, color: 'text.primary', display: 'block', textAlign: 'left', fontSize: '0.775rem' }}>
              Full Name
            </Typography>
            <TextField
              fullWidth
              placeholder="John Doe"
              variant="outlined"
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <PersonIcon sx={{ color: 'text.disabled', fontSize: 18 }} />
                    </InputAdornment>
                  ),
                  sx: { 
                    height: '38px',
                    fontSize: '0.8rem',
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
              disabled={loading || success}
            />
          </Box>

          {/* Email Address */}
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5, color: 'text.primary', display: 'block', textAlign: 'left', fontSize: '0.775rem' }}>
              Work Email
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
                  startAdornment: (
                    <InputAdornment position="start">
                      <EmailIcon sx={{ color: 'text.disabled', fontSize: 18 }} />
                    </InputAdornment>
                  ),
                  sx: { 
                    height: '38px',
                    fontSize: '0.8rem',
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
              disabled={loading || success}
            />
          </Box>

          {/* Company Name */}
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5, color: 'text.primary', display: 'block', textAlign: 'left', fontSize: '0.775rem' }}>
              Company Name
            </Typography>
            <TextField
              fullWidth
              placeholder="Acme Corp (Optional)"
              variant="outlined"
              type="text"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <CorporateFareIcon sx={{ color: 'text.disabled', fontSize: 18 }} />
                    </InputAdornment>
                  ),
                  sx: { 
                    height: '38px',
                    fontSize: '0.8rem',
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
              disabled={loading || success}
            />
          </Box>

          {/* Assigned Role */}
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5, color: 'text.primary', display: 'block', textAlign: 'left', fontSize: '0.775rem' }}>
              Assigned User Role
            </Typography>
            <TextField
              select
              fullWidth
              variant="outlined"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <BadgeIcon sx={{ color: 'text.disabled', mr: 1, fontSize: 18 }} />
                    </InputAdornment>
                  ),
                  sx: { 
                    height: '38px',
                    fontSize: '0.8rem',
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
              disabled={loading || success}
            >
              <MenuItem value="Viewer" sx={{ fontSize: '0.8rem' }}>Viewer (Read Only)</MenuItem>
              <MenuItem value="Auditor" sx={{ fontSize: '0.8rem' }}>Auditor (Run scans)</MenuItem>
              <MenuItem value="Admin" sx={{ fontSize: '0.8rem' }}>Admin (Full scope)</MenuItem>
            </TextField>
          </Box>

          {/* Password */}
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5, color: 'text.primary', display: 'block', textAlign: 'left', fontSize: '0.775rem' }}>
              Password
            </Typography>
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
                  startAdornment: (
                    <InputAdornment position="start">
                      <LockIcon sx={{ color: 'text.disabled', fontSize: 18 }} />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton onClick={() => setShowPassword(!showPassword)} edge="end" size="small">
                        {showPassword ? <VisibilityOff sx={{ fontSize: 18 }} /> : <Visibility sx={{ fontSize: 18 }} />}
                      </IconButton>
                    </InputAdornment>
                  ),
                  sx: { 
                    height: '38px',
                    fontSize: '0.8rem',
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
              disabled={loading || success}
            />
          </Box>

          {/* Agreement Checkbox */}
          <FormControlLabel 
            control={
              <Checkbox 
                checked={agree}
                onChange={(e) => setAgree(e.target.checked)}
                sx={{ 
                  color: 'text.disabled', 
                  '&.Mui-checked': { color: 'primary.main' },
                  p: 0.25
                }} 
              />
            } 
            label={
              <Typography variant="body2" sx={{ color: 'text.secondary', fontWeight: 500, userSelect: 'none', ml: 0.25, textAlign: 'left', fontSize: '0.725rem', lineHeight: 1.25 }}>
                I agree to the <MuiLink href="#" sx={{ color: 'primary.main', fontWeight: 600, textDecoration: 'none' }}>Terms</MuiLink> and <MuiLink href="#" sx={{ color: 'primary.main', fontWeight: 600, textDecoration: 'none' }}>Privacy Policy</MuiLink>.
              </Typography>
            } 
            sx={{ m: 0, alignItems: 'center' }}
          />

          {/* Register Button */}
          <Button
            type="submit"
            variant="contained"
            size="medium"
            fullWidth
            endIcon={<ArrowForwardIcon sx={{ fontSize: '0.9rem !important' }} />}
            sx={{ 
              py: 0.9, 
              borderRadius: '8px', 
              fontWeight: '600',
              fontSize: '0.8rem',
              textTransform: 'none',
              bgcolor: 'primary.main',
              '&:hover': {
                bgcolor: 'primary.dark',
              }
            }}
            disabled={loading || success}
          >
            {loading ? <CircularProgress size={18} color="inherit" /> : 'Create Account'}
          </Button>
        </Stack>
      </form>
    </Paper>
  );
};

export default RegisterForm;
