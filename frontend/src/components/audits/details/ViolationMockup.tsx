import React from 'react';
import { Box, Typography, Chip } from '@mui/material';

interface ViolationMockupProps {
  htmlSnippet: string;
  ruleId: string;
}

export const ViolationMockup: React.FC<ViolationMockupProps> = ({ htmlSnippet, ruleId }) => {
  const getTagType = (html: string) => {
    const match = html.trim().match(/^<([a-zA-Z0-9]+)/);
    return match ? match[1].toLowerCase() : 'element';
  };

  const tag = getTagType(htmlSnippet);

  return (
    <Box sx={{
      border: '1px solid #e2e8f0',
      borderRadius: '12px',
      overflow: 'hidden',
      bgcolor: '#f8fafc',
      boxShadow: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.02)'
    }}>
      {/* Browser Bar */}
      <Box sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        px: 2,
        py: 1.5,
        bgcolor: '#f1f5f9',
        borderBottom: '1px solid #e2e8f0'
      }}>
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: '#ef4444' }} />
          <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: '#f59e0b' }} />
          <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: '#10b981' }} />
        </Box>
        <Box sx={{
          flex: 1,
          bgcolor: '#ffffff',
          borderRadius: '6px',
          px: 1.5,
          py: 0.5,
          fontSize: '0.75rem',
          color: 'text.secondary',
          fontFamily: 'monospace',
          border: '1px solid #cbd5e1',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap'
        }}>
          Render Preview
        </Box>
      </Box>

      {/* Preview Body */}
      <Box sx={{
        p: 4,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '220px',
        position: 'relative'
      }}>
        <Box sx={{
          border: '2px dashed #ef4444',
          borderRadius: '8px',
          p: 3,
          position: 'relative',
          bgcolor: '#ffffff',
          boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 1.5,
          maxWidth: '85%'
        }}>
          {/* Violation Area Badge */}
          <Chip
            label="VIOLATION AREA"
            size="small"
            sx={{
              bgcolor: '#ef4444',
              color: '#ffffff',
              fontWeight: '800',
              fontSize: '0.65rem',
              height: '18px',
              position: 'absolute',
              top: -10,
              right: 10,
              boxShadow: 2
            }}
          />

          {tag === 'img' && (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
              <Box sx={{ width: 64, height: 64, bgcolor: '#e2e8f0', borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '2rem' }}>
                📷
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: '600' }}>Missing Alt Attribute</Typography>
            </Box>
          )}

          {(tag === 'button' || tag === 'a') && (
            <Box sx={{ px: 3, py: 1, bgcolor: '#0284c7', color: '#ffffff', borderRadius: '6px', fontWeight: '600', fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Interactive Node
            </Box>
          )}

          {tag === 'input' && (
            <Box sx={{ width: 160, height: 36, border: '1px solid #cbd5e1', borderRadius: '6px', px: 1.5, display: 'flex', alignItems: 'center', bgcolor: '#f8fafc' }}>
              <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#cbd5e1' }} />
            </Box>
          )}

          {tag !== 'img' && tag !== 'button' && tag !== 'a' && tag !== 'input' && (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" sx={{ fontWeight: '700', color: 'text.primary', textAlign: 'center' }}>
                {ruleId.replace(/-/g, ' ').toUpperCase()}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ textAlign: 'center', wordBreak: 'break-all', fontFamily: 'monospace' }}>
                {htmlSnippet.length > 100 ? htmlSnippet.substring(0, 100) + '...' : htmlSnippet}
              </Typography>
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
};
