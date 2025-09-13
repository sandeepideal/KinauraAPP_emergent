import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null,
      errorInfo: null 
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details for debugging
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo
    });

    // Log to monitoring service if available
    if (window.gtag) {
      window.gtag('event', 'exception', {
        description: error?.message || 'Unknown error',
        fatal: true
      });
    }
  }

  handleReload = () => {
    window.location.reload();
  };

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      // Custom error UI
      return (
        <div className="min-h-screen bg-ka-bg flex items-center justify-center p-6">
          <div className="ka-card max-w-lg w-full text-center">
            <div className="mb-6">
              {/* Error Icon */}
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg 
                  className="w-8 h-8 text-red-600" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5l-6.928-12c-.77-.833-2.694-.833-3.464 0L1.732 16.5C.962 18.333 1.924 20 3.464 20z" 
                  />
                </svg>
              </div>
              
              <h1 className="ka-heading-2 text-ka-text mb-2">Something went wrong</h1>
              <p className="ka-body-lg text-ka-text-2 mb-6">
                We apologize for the inconvenience. An unexpected error has occurred.
              </p>
            </div>

            <div className="space-y-3 mb-6">
              <button
                onClick={this.handleReset}
                className="ka-button w-full"
              >
                Try Again
              </button>
              
              <button
                onClick={this.handleReload}
                className="ka-outline w-full"
              >
                Reload Page
              </button>
            </div>

            {/* Error Details (Development only) */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="text-left">
                <summary className="cursor-pointer text-sm text-ka-text-2 mb-2">
                  Show Error Details
                </summary>
                <div className="bg-ka-muted p-4 rounded-md text-xs font-mono overflow-auto max-h-40">
                  <div className="text-red-600 font-bold mb-2">
                    {this.state.error.toString()}
                  </div>
                  <div className="text-ka-text-2 whitespace-pre-wrap">
                    {this.state.errorInfo?.componentStack}
                  </div>
                </div>
              </details>
            )}

            {/* Support Information */}
            <div className="text-xs text-ka-text-2 pt-4 border-t border-ka-stone-200">
              <p>
                If this problem persists, please contact our support team at{' '}
                <a 
                  href="mailto:support@kinaura.com" 
                  className="text-ka-brand hover:underline"
                >
                  support@kinaura.com
                </a>
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;