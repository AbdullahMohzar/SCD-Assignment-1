import React from 'react';
import { Priority } from '../api/types';

interface PriorityBadgeProps {
  priority: Priority;
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority }) => {
  let badgeClass = 'badge-gray';

  switch (priority) {
    case 'high':
      badgeClass = 'badge-red';
      break;
    case 'normal':
      badgeClass = 'badge-blue';
      break;
    case 'low':
      badgeClass = 'badge-gray';
      break;
  }

  return (
    <span className={`badge ${badgeClass}`} data-testid={`priority-badge-${priority}`}>
      {priority}
    </span>
  );
};
