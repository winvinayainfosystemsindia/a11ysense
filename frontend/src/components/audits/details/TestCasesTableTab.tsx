import React from 'react';
import { Chip, Typography, TableRow, TableCell } from '@mui/material';
import DataTable from '../../common/table/DataTable';
import type { ColumnDefinition } from '../../common/table/DataTable';

interface TestCasesTableTabProps {
  testcases: any[];
  testcasesPage: number;
  setTestcasesPage: (p: number) => void;
  testcasesRowsPerPage: number;
  setTestcasesRowsPerPage: (r: number) => void;
}

const COLUMNS: ColumnDefinition<any>[] = [
  { id: 'testcase_id', label: 'TC ID', sortable: false, align: 'left' },
  { id: 'testcase_name', label: 'Test Name', sortable: false, align: 'left' },
  { id: 'rule_id', label: 'Rule ID', sortable: false, align: 'left' },
  { id: 'status', label: 'Status', sortable: false, align: 'left' },
  { id: 'page_title', label: 'Page', sortable: false, align: 'left' }
];

export const TestCasesTableTab: React.FC<TestCasesTableTabProps> = ({
  testcases,
  testcasesPage,
  setTestcasesPage,
  testcasesRowsPerPage,
  setTestcasesRowsPerPage
}) => {
  const paginatedData = testcases.slice(
    testcasesPage * testcasesRowsPerPage,
    testcasesPage * testcasesRowsPerPage + testcasesRowsPerPage
  );

  const renderRow = (tc: any) => (
    <TableRow key={tc.testcase_id} hover>
      <TableCell sx={{ fontWeight: '600', fontSize: '0.8rem' }}>{tc.testcase_id}</TableCell>
      <TableCell>
        <Typography variant="subtitle2" sx={{ fontWeight: '700' }}>{tc.testcase_name}</Typography>
        <Typography variant="caption" color="text.secondary">{tc.description}</Typography>
      </TableCell>
      <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{tc.rule_id}</TableCell>
      <TableCell>
        <Chip 
          label={tc.status} 
          color={tc.status === 'PASS' ? 'success' : 'error'} 
          size="small" 
          sx={{ fontWeight: '700', fontSize: '0.7rem' }} 
        />
      </TableCell>
      <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>{tc.page_title}</TableCell>
    </TableRow>
  );

  return (
    <DataTable<any>
      columns={COLUMNS}
      data={paginatedData}
      totalCount={testcases.length}
      page={testcasesPage}
      rowsPerPage={testcasesRowsPerPage}
      onPageChange={(_, page) => setTestcasesPage(page)}
      onRowsPerPageChange={(newRowsPerPage) => {
        setTestcasesRowsPerPage(newRowsPerPage);
        setTestcasesPage(0);
      }}
      searchTerm=""
      emptyMessage="No test checks ran."
      renderRow={renderRow}
    />
  );
};
