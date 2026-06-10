import React from 'react';
import {
  Card,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Chip,
  alpha
} from '@mui/material';
import type { Transaction } from '../../service/billingService';

interface BillingHistoryTableProps {
  transactions: Transaction[];
}

const BillingHistoryTable: React.FC<BillingHistoryTableProps> = ({ transactions }) => {
  return (
    <Card variant="outlined" sx={{ bgcolor: 'background.paper', borderRadius: '12px', height: '100%' }}>
      <Typography variant="h6" sx={{ fontWeight: '700', p: 3, pb: 2 }}>
        Billing History
      </Typography>
      <TableContainer>
        <Table sx={{ minWidth: 400 }}>
          <TableHead>
            <TableRow sx={{ bgcolor: (theme) => alpha(theme.palette.primary.main, 0.03) }}>
              <TableCell sx={{ fontWeight: '700', color: 'text.secondary' }}>INVOICE</TableCell>
              <TableCell sx={{ fontWeight: '700', color: 'text.secondary' }}>DATE</TableCell>
              <TableCell sx={{ fontWeight: '700', color: 'text.secondary' }}>AMOUNT</TableCell>
              <TableCell sx={{ fontWeight: '700', color: 'text.secondary' }}>STATUS</TableCell>
              <TableCell align="right" sx={{ fontWeight: '700', color: 'text.secondary' }}></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {transactions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                  <Typography variant="body2" color="text.secondary">No billing history found.</Typography>
                </TableCell>
              </TableRow>
            ) : (
              transactions.map((invoice) => (
                <TableRow key={invoice.id} sx={{ '&:last-child td, &:last-child th': { border: 0 }, '&:hover': { bgcolor: (theme) => alpha(theme.palette.primary.main, 0.01) } }}>
                  <TableCell>
                    <Typography variant="subtitle2" sx={{ fontWeight: '600' }}>
                      {invoice.id.split('-')[0]}...
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {new Date(invoice.timestamp).toLocaleDateString()}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: '600' }}>
                      {invoice.amount.toLocaleString()} credits
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={invoice.transaction_type.toUpperCase()}
                      size="small"
                      color={invoice.transaction_type === 'purchase' ? 'success' : 'default'}
                      sx={{ fontWeight: '700', fontSize: '0.7rem' }}
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="caption" color="text.secondary">{invoice.description}</Typography>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Card>
  );
};

export default BillingHistoryTable;
