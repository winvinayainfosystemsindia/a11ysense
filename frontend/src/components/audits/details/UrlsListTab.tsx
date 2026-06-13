import React from 'react';
import { Card, Stack, Box, Typography, TableRow, TableCell, Chip, IconButton, Grid } from '@mui/material';
import LaunchIcon from '@mui/icons-material/Launch';
import type { AuditTaskDetail } from '../../../service/auditService';
import DataTable from '../../common/table/DataTable';
import type { ColumnDefinition } from '../../common/table/DataTable';

interface UrlsListTabProps {
  taskDetail: AuditTaskDetail;
  urlSearchQuery: string;
  setUrlSearchQuery: (q: string) => void;
  filteredDiscoveredUrls: string[];
  urlsPage: number;
  setUrlsPage: (p: number) => void;
  urlsRowsPerPage: number;
  setUrlsRowsPerPage: (r: number) => void;
}

const COLUMNS: ColumnDefinition<any>[] = [
  { id: 'urlIndex', label: '#', sortable: false, width: '80px' },
  { id: 'page_url', label: 'PAGE URL', sortable: false },
  { id: 'depth', label: 'DEPTH', sortable: false, width: '100px' },
  { id: 'status', label: 'STATUS', sortable: false, width: '150px' },
  { id: 'actions', label: 'ACTION', sortable: false, align: 'right', width: '120px' }
];

export const UrlsListTab: React.FC<UrlsListTabProps> = ({
  taskDetail,
  urlSearchQuery,
  setUrlSearchQuery,
  filteredDiscoveredUrls,
  urlsPage,
  setUrlsPage,
  urlsRowsPerPage,
  setUrlsRowsPerPage
}) => {
  const paginatedData = filteredDiscoveredUrls
    .slice(urlsPage * urlsRowsPerPage, urlsPage * urlsRowsPerPage + urlsRowsPerPage)
    .map((urlStr, index) => ({
      urlStr,
      urlIndex: urlsPage * urlsRowsPerPage + index + 1
    }));

  const renderRow = (item: { urlStr: string; urlIndex: number }) => {
    const isScanned = taskDetail.pages_scanned?.includes(item.urlStr) || 
      taskDetail.pages_scanned?.some(scanned => scanned === item.urlStr || scanned.replace(/\/$/, '') === item.urlStr.replace(/\/$/, ''));
    const pageDepth = taskDetail.pages_depth_map?.[item.urlStr] ?? 1;

    return (
      <TableRow key={item.urlStr} hover>
        <TableCell sx={{ fontFamily: 'monospace', color: 'text.secondary' }}>
          {item.urlIndex}
        </TableCell>
        <TableCell sx={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
          {item.urlStr}
        </TableCell>
        <TableCell>
          <Chip
            label={`Depth ${pageDepth}`}
            variant="outlined"
            size="small"
            sx={{ fontWeight: '600', borderRadius: '6px', fontSize: '0.65rem' }}
          />
        </TableCell>
        <TableCell>
          <Chip
            label={isScanned ? 'SCANNED' : 'DISCOVERED'}
            color={isScanned ? 'success' : 'default'}
            size="small"
            sx={{ fontWeight: '700', borderRadius: '6px', fontSize: '0.65rem' }}
          />
        </TableCell>
        <TableCell align="right">
          <IconButton
            size="small"
            component="a"
            href={item.urlStr}
            target="_blank"
            rel="noopener noreferrer"
            sx={{ color: 'primary.main' }}
            title="Open Page in New Tab"
          >
            <LaunchIcon sx={{ fontSize: '1.1rem' }} />
          </IconButton>
        </TableCell>
      </TableRow>
    );
  };

  return (
    <Card variant="outlined" sx={{ p: 4, borderRadius: '16px' }}>
      <Stack component="div" spacing={3}>
        <Box>
          <Typography variant="h5" sx={{ fontWeight: '800', fontFamily: 'Outfit', mb: 1 }}>
            List of Site URLs
          </Typography>
          <Typography variant="body2" color="text.secondary">
            View the full list of pages discovered and scanned during the audit run.
          </Typography>
        </Box>

        {/* Sub-Metrics Panel */}
        <Grid container spacing={3} sx={{ bgcolor: '#f8fafc', p: 2, borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <Grid size={{ xs: 12, sm: 4 }}>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontWeight: '700', textTransform: 'uppercase' }}>Crawl Depth</Typography>
            <Typography variant="h5" sx={{ fontWeight: '800', mt: 0.5 }}>{taskDetail.depth ?? 1}</Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 4 }}>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontWeight: '700', textTransform: 'uppercase' }}>URLs Discovered</Typography>
            <Typography variant="h5" sx={{ fontWeight: '800', mt: 0.5 }}>{taskDetail.pages_found ?? taskDetail.pages_discovered?.length ?? 0}</Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 4 }}>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontWeight: '700', textTransform: 'uppercase' }}>URLs Scanned</Typography>
            <Typography variant="h5" sx={{ fontWeight: '800', mt: 0.5, color: 'success.main' }}>{taskDetail.pages_completed ?? taskDetail.pages_scanned?.length ?? 0}</Typography>
          </Grid>
        </Grid>

        {/* URLs Table / List */}
        <DataTable<{ urlStr: string; urlIndex: number }>
          columns={COLUMNS}
          data={paginatedData}
          totalCount={filteredDiscoveredUrls.length}
          page={urlsPage}
          rowsPerPage={urlsRowsPerPage}
          onPageChange={(_, page) => setUrlsPage(page)}
          onRowsPerPageChange={(newRowsPerPage) => {
            setUrlsRowsPerPage(newRowsPerPage);
            setUrlsPage(0);
          }}
          searchTerm={urlSearchQuery}
          onSearchChange={(val) => {
            setUrlSearchQuery(val);
            setUrlsPage(0);
          }}
          searchPlaceholder="Search discovered URLs..."
          emptyMessage="No URLs found matching your search."
          renderRow={renderRow}
        />
      </Stack>
    </Card>
  );
};
