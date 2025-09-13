import React from 'react';

/**
 * Empty state component for when there's no data to display
 */
const EmptyState = ({ 
  icon,
  title,
  description,
  action,
  className = ''
}) => {
  return (
    <div className={`text-center py-12 px-6 ${className}`}>
      {/* Icon */}
      {icon && (
        <div className="w-16 h-16 mx-auto mb-4 flex items-center justify-center bg-ka-muted rounded-full">
          {typeof icon === 'string' ? (
            <span className="text-2xl">{icon}</span>
          ) : (
            <div className="w-8 h-8 text-ka-text-2">
              {icon}
            </div>
          )}
        </div>
      )}
      
      {/* Title */}
      {title && (
        <h3 className="ka-heading-2 text-ka-text mb-2">
          {title}
        </h3>
      )}
      
      {/* Description */}
      {description && (
        <p className="ka-body-lg text-ka-text-2 mb-6 max-w-md mx-auto">
          {description}
        </p>
      )}
      
      {/* Action */}
      {action && (
        <div>
          {action}
        </div>
      )}
    </div>
  );
};

/**
 * Predefined empty states for common scenarios
 */
export const EmptyStates = {
  NoData: ({ onRetry, actionText = "Try Again" }) => (
    <EmptyState
      icon="📊"
      title="No Data Available"
      description="There's no data to display at the moment."
      action={onRetry && (
        <button onClick={onRetry} className="ka-button">
          {actionText}
        </button>
      )}
    />
  ),

  NoResults: ({ onClear, searchTerm = "" }) => (
    <EmptyState
      icon="🔍"
      title="No Results Found"
      description={searchTerm 
        ? `No results found for "${searchTerm}". Try adjusting your search.`
        : "No results match your current filters."
      }
      action={onClear && (
        <button onClick={onClear} className="ka-outline">
          Clear Filters
        </button>
      )}
    />
  ),

  NoAppointments: ({ onBook }) => (
    <EmptyState
      icon="📅"
      title="No Appointments"
      description="You haven't booked any appointments yet. Start your wellness journey today."
      action={onBook && (
        <button onClick={onBook} className="ka-button">
          Book Your First Appointment
        </button>
      )}
    />
  ),

  NoServices: ({ onRefresh }) => (
    <EmptyState
      icon="✨"
      title="No Services Available"
      description="Our services are currently being updated. Please check back soon."
      action={onRefresh && (
        <button onClick={onRefresh} className="ka-outline">
          Refresh
        </button>
      )}
    />
  ),

  NoConnections: ({ onConnect }) => (
    <EmptyState
      icon="📱"
      title="No Devices Connected"
      description="Connect your Apple Health or WHOOP to start tracking your wellness metrics."
      action={onConnect && (
        <button onClick={onConnect} className="ka-button">
          Connect Device
        </button>
      )}
    />
  ),

  Error: ({ onRetry, message = "Something went wrong. Please try again." }) => (
    <EmptyState
      icon={
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-full h-full">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5l-6.928-12c-.77-.833-2.694-.833-3.464 0L1.732 16.5C.962 18.333 1.924 20 3.464 20z" />
        </svg>
      }
      title="Something Went Wrong"
      description={message}
      action={onRetry && (
        <button onClick={onRetry} className="ka-button">
          Try Again
        </button>
      )}
    />
  )
};

export default EmptyState;