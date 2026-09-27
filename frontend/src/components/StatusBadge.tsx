import React from 'react';
import { Status } from '../api/types';

interface StatusBadgeProps {
  status: Status;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  let badgeClass = 'badge-gray';
  let label = status.replace('_', ' ');

  switch (status) {
    case 'open':
      badgeClass = 'badge-blue';
      break;
    case 'in_progress':
      badgeClass = 'badge-yellow';
      break;
    case 'resolved':
      badgeClass = 'badge-green';
      break;
    case 'rejected':
      badgeClass = 'badge-red';
      break;
  }

  return (
    <span className={`badge ${badgeClass}`} data-testid={`status-badge-${status}`}>
      {label}
    </span>
  );
};
