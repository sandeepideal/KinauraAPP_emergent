import React from 'react';

/**
 * Skeleton loading component with shimmer animation
 * Used to show placeholders while data is loading
 */
const Skeleton = ({ 
  width = '100%', 
  height = '20px', 
  className = '',
  variant = 'rectangular' // rectangular, circular, text
}) => {
  const baseClasses = 'animate-shimmer bg-gradient-to-r from-ka-stone-200 via-ka-stone-100 to-ka-stone-200 bg-[length:200%_100%]';
  
  const variantClasses = {
    rectangular: 'rounded-md',
    circular: 'rounded-full',
    text: 'rounded-sm'
  };

  const style = {
    width,
    height
  };

  return (
    <div 
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      style={style}
      aria-label="Loading..."
    />
  );
};

/**
 * Skeleton for card layouts
 */
export const SkeletonCard = ({ className = '' }) => (
  <div className={`ka-card animate-pulse ${className}`}>
    <div className="flex items-center space-x-4 mb-4">
      <Skeleton variant="circular" width="48px" height="48px" />
      <div className="space-y-2 flex-1">
        <Skeleton width="60%" height="16px" />
        <Skeleton width="40%" height="14px" />
      </div>
    </div>
    <div className="space-y-2">
      <Skeleton width="100%" height="14px" />
      <Skeleton width="80%" height="14px" />
      <Skeleton width="90%" height="14px" />
    </div>
  </div>
);

/**
 * Skeleton for list items
 */
export const SkeletonListItem = ({ className = '' }) => (
  <div className={`flex items-center space-x-3 p-4 ${className}`}>
    <Skeleton variant="circular" width="40px" height="40px" />
    <div className="flex-1 space-y-2">
      <Skeleton width="70%" height="16px" />
      <Skeleton width="50%" height="14px" />
    </div>
    <Skeleton width="80px" height="32px" />
  </div>
);

/**
 * Skeleton for data table rows
 */
export const SkeletonTableRow = ({ columns = 4, className = '' }) => (
  <tr className={className}>
    {Array.from({ length: columns }, (_, i) => (
      <td key={i} className="px-4 py-3">
        <Skeleton width="80%" height="16px" />
      </td>
    ))}
  </tr>
);

/**
 * Loading state with multiple skeletons
 */
export const SkeletonLoader = ({ 
  count = 3, 
  variant = 'card',
  className = '' 
}) => {
  const SkeletonComponent = {
    card: SkeletonCard,
    list: SkeletonListItem,
    text: Skeleton
  }[variant] || SkeletonCard;

  return (
    <div className={`space-y-4 ${className}`}>
      {Array.from({ length: count }, (_, i) => (
        <SkeletonComponent key={i} />
      ))}
    </div>
  );
};

export default Skeleton;