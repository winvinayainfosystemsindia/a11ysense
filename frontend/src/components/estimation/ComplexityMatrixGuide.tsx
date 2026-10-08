import React from 'react';
import {
  Box,
  Typography,
  Stack,
  Card,
  CardContent,
  Grid,
  Button,
  Collapse,
  useTheme,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import BoltIcon from '@mui/icons-material/Bolt';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

interface ComplexityMatrixGuideProps {
  expanded: boolean;
  onToggle: () => void;
}

export const ComplexityMatrixGuide: React.FC<ComplexityMatrixGuideProps> = ({
  expanded,
  onToggle,
}) => {
  const theme = useTheme();

  return (
    <Box sx={{ mb: 4 }}>
      <Button
        variant="text"
        color="inherit"
        onClick={onToggle}
        startIcon={<InfoOutlinedIcon color="primary" />}
        endIcon={expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        sx={{
          fontWeight: 700,
          textTransform: 'none',
          px: 0,
          mb: 1,
          color: theme.palette.text.primary,
          '&:hover': {
            bgcolor: 'transparent',
            color: theme.palette.primary.main,
          },
        }}
      >
        {expanded
          ? 'Hide Complexity Classification Matrix'
          : 'View Complexity Classification Matrix (Simple, Medium, Complex)'}
      </Button>

      <Collapse in={expanded}>
        <Grid container spacing={2.5} component="div" sx={{ mt: 0.5 }}>
          {/* Simple Card */}
          <Grid size={{ xs: 12, md: 4 }} component="div">
            <Card
              sx={{
                bgcolor: alpha(theme.palette.success.main, 0.05),
                border: `1px solid ${alpha(theme.palette.success.main, 0.25)}`,
                borderRadius: 3,
                boxShadow: 'none',
              }}
            >
              <CardContent sx={{ p: 2.5 }}>
                <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1.5 }}>
                  <CheckCircleIcon sx={{ color: theme.palette.success.main, fontSize: 20 }} />
                  <Typography variant="subtitle1" sx={{ fontWeight: 800, color: theme.palette.success.dark }}>
                    Simple: Static Content (~1.0 Hr)
                  </Typography>
                </Stack>
                <Typography variant="body2" sx={{ color: theme.palette.success.dark, lineHeight: 1.6 }}>
                  • Read top-to-bottom with no state mutations<br />
                  • Standard headings, paragraphs, and list hierarchies<br />
                  • Plain links (header, footer, basic navigational bar)<br />
                  • Informative/decorative images and plain buttons<br />
                  • <strong>Total no. of Elements ≤ 50</strong>
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Medium Card */}
          <Grid size={{ xs: 12, md: 4 }} component="div">
            <Card
              sx={{
                bgcolor: alpha(theme.palette.warning.main, 0.05),
                border: `1px solid ${alpha(theme.palette.warning.main, 0.28)}`,
                borderRadius: 3,
                boxShadow: 'none',
              }}
            >
              <CardContent sx={{ p: 2.5 }}>
                <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1.5 }}>
                  <WarningAmberIcon sx={{ color: theme.palette.warning.main, fontSize: 20 }} />
                  <Typography variant="subtitle1" sx={{ fontWeight: 800, color: theme.palette.warning.dark }}>
                    Medium: Standard Interaction (~2.5 Hrs)
                  </Typography>
                </Stack>
                <Typography variant="body2" sx={{ color: theme.palette.warning.dark, lineHeight: 1.6 }}>
                  • Basic forms (inputs, selects, checkboxes, submit)<br />
                  • Data tables with row and column headers<br />
                  • Single embedded video, audio player, or map iframe<br />
                  • Expanding navigation (dropdowns, accordions, tabs)<br />
                  • Search box or <strong>Total no. of Elements &gt; 50 and ≤ 90</strong>
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Complex Card */}
          <Grid size={{ xs: 12, md: 4 }} component="div">
            <Card
              sx={{
                bgcolor: alpha(theme.palette.error.main, 0.05),
                border: `1px solid ${alpha(theme.palette.error.main, 0.25)}`,
                borderRadius: 3,
                boxShadow: 'none',
              }}
            >
              <CardContent sx={{ p: 2.5 }}>
                <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1.5 }}>
                  <BoltIcon sx={{ color: theme.palette.error.main, fontSize: 20 }} />
                  <Typography variant="subtitle1" sx={{ fontWeight: 800, color: theme.palette.error.dark }}>
                    Complex: Dynamic Widgets (~5.5 Hrs)
                  </Typography>
                </Stack>
                <Typography variant="body2" sx={{ color: theme.palette.error.dark, lineHeight: 1.6 }}>
                  • Pop-up dialogs, cookie banners, focus-shifting modals<br />
                  • Custom widgets (sliders, date pickers, trees, drag-drop)<br />
                  • Multi-step checkout, authentication/OTP/CAPTCHA<br />
                  • Moving content, carousels, live tickers, maps, charts<br />
                  • Complex tables (merged cells, sortable headers)
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Collapse>
    </Box>
  );
};
