import React from 'react';
import {
  Chip,
  Typography,
  TableRow,
  TableCell,
  Stack,
  IconButton,
  Box,
  Button
} from '@mui/material';
import LaunchIcon from '@mui/icons-material/Launch';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DataTable from '../../common/table/DataTable';
import type { ColumnDefinition } from '../../common/table/DataTable';

interface DefectsTableTabProps {
  violations: any[];
  defectsPage: number;
  setDefectsPage: (p: number) => void;
  defectsRowsPerPage: number;
  setDefectsRowsPerPage: (r: number) => void;
  taskId: string;
  handleCopyCode: (code: string) => void;
  setSelectedViolation: (v: any) => void;
  setActiveTab: (t: number) => void;
}

const COLUMNS: ColumnDefinition<any>[] = [
  { id: 'defectIndex', label: 'DEFECT ID', sortable: false },
  { id: 'testcase_id', label: 'ASSOCIATED TC ID', sortable: false },
  { id: 'page_title', label: 'PAGE TITLE', sortable: false },
  { id: 'page_url', label: 'URL', sortable: false },
  { id: 'criteria', label: 'CRITERIA', sortable: false },
  { id: 'level', label: 'LEVEL', sortable: false },
  { id: 'severity', label: 'SEVERITY', sortable: false },
  { id: 'description', label: 'DESCRIPTION', sortable: false },
  { id: 'expected_result', label: 'EXPECTED', sortable: false },
  { id: 'actual_result', label: 'ACTUAL', sortable: false },
  { id: 'steps_to_reproduce', label: 'STEPS TO REPRODUCE', sortable: false },
  { id: 'remediation', label: 'REMEDIATION', sortable: false },
  { id: 'help_url', label: 'HELP', sortable: false },
  { id: 'html_snippet', label: 'HTML SNIPPET', sortable: false },
  { id: 'screenshot', label: 'SCREENSHOT', sortable: false },
  { id: 'actions', label: 'INSPECT', sortable: false, align: 'right' }
];

export const DefectsTableTab: React.FC<DefectsTableTabProps> = ({
  violations,
  defectsPage,
  setDefectsPage,
  defectsRowsPerPage,
  setDefectsRowsPerPage,
  taskId,
  handleCopyCode,
  setSelectedViolation,
  setActiveTab
}) => {
  const paginatedData = violations
    .slice(defectsPage * defectsRowsPerPage, defectsPage * defectsRowsPerPage + defectsRowsPerPage)
    .map((v, idx) => ({
      ...v,
      defectIndex: defectsPage * defectsRowsPerPage + idx + 1
    }));

  const renderRow = (v: any) => {
    const sevColor = v.severity?.toLowerCase() === 'critical' ? 'error' : v.severity?.toLowerCase() === 'serious' ? 'warning' : 'info';
    return (
      <TableRow key={v.testcase_id} hover>
        {/* 1. Defect ID */}
        <TableCell sx={{ fontWeight: 'bold', fontFamily: 'monospace', whiteSpace: 'nowrap' }}>
          DEF-{String(v.defectIndex).padStart(3, '0')}
        </TableCell>

        {/* 2. Associated Testcase ID */}
        <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.8rem', whiteSpace: 'nowrap' }}>
          {v.testcase_id}
        </TableCell>

        {/* 3. Page Title */}
        <TableCell sx={{ minWidth: 150 }}>
          {v.page_title}
        </TableCell>

        {/* 4. URL */}
        <TableCell sx={{ minWidth: 180 }}>
          <Stack component="div" direction="row" spacing={0.5} sx={{ alignItems: 'center' }}>
            <Typography variant="body2" sx={{
              fontFamily: 'monospace',
              fontSize: '0.8rem',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              maxWidth: 200,
              display: 'block'
            }}>
              {v.page_url}
            </Typography>
            <IconButton size="small" component="a" href={v.page_url} target="_blank" rel="noopener noreferrer">
              <LaunchIcon sx={{ fontSize: '0.9rem' }} />
            </IconButton>
          </Stack>
        </TableCell>

        {/* 5. Criteria */}
        <TableCell sx={{ whiteSpace: 'nowrap' }}>
          <Chip label={v.criteria} size="small" variant="outlined" sx={{ fontWeight: '600', fontSize: '0.75rem' }} />
        </TableCell>

        {/* 6. Level */}
        <TableCell>
          <Chip label={v.level} size="small" sx={{ fontWeight: 'bold', fontSize: '0.75rem', bgcolor: '#f1f5f9' }} />
        </TableCell>

        {/* 7. Severity */}
        <TableCell>
          <Chip label={v.severity?.toUpperCase() || 'MODERATE'} color={sevColor} size="small" sx={{ fontWeight: '700', fontSize: '0.65rem' }} />
        </TableCell>

        {/* 8. Description */}
        <TableCell sx={{ minWidth: 250 }}>
          <Box sx={{ fontSize: '0.875rem', pr: 1 }}>
            {v.description}
          </Box>
        </TableCell>

        {/* 9. Expected */}
        <TableCell sx={{ minWidth: 220 }}>
          <Box sx={{ fontSize: '0.875rem', pr: 1, color: 'text.secondary' }}>
            {v.expected_result}
          </Box>
        </TableCell>

        {/* 10. Actual */}
        <TableCell sx={{ minWidth: 220 }}>
          <Box sx={{ fontSize: '0.875rem', pr: 1, color: 'error.main' }}>
            {v.actual_result}
          </Box>
        </TableCell>

        {/* 11. Steps to Reproduce */}
        <TableCell sx={{ minWidth: 250 }}>
          <Box sx={{ fontSize: '0.875rem', pr: 1, whiteSpace: 'pre-line' }}>
            {v.steps_to_reproduce}
          </Box>
        </TableCell>

        {/* 12. Remediation */}
        <TableCell sx={{ minWidth: 250 }}>
          <Box sx={{
            fontFamily: 'monospace',
            fontSize: '0.8rem',
            p: 1,
            borderRadius: 1,
            bgcolor: '#f8fafc',
            border: '1px solid #e2e8f0',
            whiteSpace: 'pre-wrap',
            color: '#0f766e'
          }}>
            {v.remediation}
          </Box>
        </TableCell>

        {/* 13. Help */}
        <TableCell>
          {v.help_url ? (
            <Button
              size="small"
              startIcon={<LaunchIcon />}
              href={v.help_url}
              target="_blank"
              rel="noopener noreferrer"
              sx={{ textTransform: 'none', whiteSpace: 'nowrap', fontWeight: '700' }}
            >
              Rule Help
            </Button>
          ) : (
            'N/A'
          )}
        </TableCell>

        {/* 14. HTML Snippet */}
        <TableCell sx={{ minWidth: 300 }}>
          {v.html_snippet ? (
            <Stack component="div" direction="row" spacing={1} sx={{ alignItems: 'flex-start' }}>
              <Box sx={{
                fontFamily: 'monospace',
                fontSize: '0.8rem',
                p: 1,
                borderRadius: 1,
                bgcolor: '#0f172a',
                color: '#fb7185',
                flex: 1,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-all'
              }}>
                {v.html_snippet}
              </Box>
              <IconButton size="small" onClick={() => handleCopyCode(v.html_snippet)} sx={{ color: 'text.secondary' }}>
                <ContentCopyIcon fontSize="inherit" />
              </IconButton>
            </Stack>
          ) : (
            'N/A'
          )}
        </TableCell>

        {/* 14b. Screenshot */}
        <TableCell sx={{ whiteSpace: 'nowrap' }}>
          {v.screenshot && v.screenshot !== 'N/A' ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <IconButton
                size="small"
                component="a"
                href={`http://localhost:8002/report/${taskId}/screenshot/${v.screenshot}`}
                target="_blank"
                rel="noopener noreferrer"
                title="Open full screenshot in new tab"
              >
                <LaunchIcon sx={{ fontSize: '1.1rem' }} />
              </IconButton>
              <Box
                component="img"
                src={`http://localhost:8002/report/${taskId}/screenshot/${v.screenshot}`}
                alt="Thumbnail"
                sx={{
                  width: 48,
                  height: 32,
                  objectFit: 'cover',
                  borderRadius: '4px',
                  border: '1px solid #e2e8f0',
                  cursor: 'pointer'
                }}
                onClick={() => {
                  window.open(`http://localhost:8002/report/${taskId}/screenshot/${v.screenshot}`, '_blank');
                }}
              />
            </Box>
          ) : (
            'N/A'
          )}
        </TableCell>

        {/* 15. Inspect Button */}
        <TableCell align="right">
          <Button
            size="small"
            onClick={() => {
              setSelectedViolation(v);
              setActiveTab(0);
            }}
            sx={{ textTransform: 'none', fontWeight: '700', whiteSpace: 'nowrap' }}
          >
            View
          </Button>
        </TableCell>
      </TableRow>
    );
  };

  return (
    <DataTable<any>
      columns={COLUMNS}
      data={paginatedData}
      totalCount={violations.length}
      page={defectsPage}
      rowsPerPage={defectsRowsPerPage}
      onPageChange={(_, page) => setDefectsPage(page)}
      onRowsPerPageChange={(newRowsPerPage) => {
        setDefectsRowsPerPage(newRowsPerPage);
        setDefectsPage(0);
      }}
      searchTerm=""
      emptyMessage="No violations detected!"
      renderRow={renderRow}
    />
  );
};
