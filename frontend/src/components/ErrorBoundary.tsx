import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('CivicPulse Uncaught error:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="container" style={{ paddingTop: '4rem', textAlign: 'center' }}>
          <div className="card" style={{ maxWidth: '600px', margin: '0 auto', borderColor: '#fca5a5' }}>
            <h2 style={{ color: '#b91c1c', marginBottom: '1rem', fontSize: '1.5rem' }}>
              Something went wrong
            </h2>
            <p style={{ color: '#475569', marginBottom: '1.5rem' }}>
              An unexpected application error occurred. The system safely caught this exception.
            </p>
            {this.state.error && (
              <pre
                style={{
                  background: '#f8fafc',
                  padding: '1rem',
                  borderRadius: '0.5rem',
                  fontSize: '0.875rem',
                  color: '#991b1b',
                  overflowX: 'auto',
                  marginBottom: '1.5rem',
                  textAlign: 'left',
                }}
              >
                {this.state.error.message}
              </pre>
            )}
            <button onClick={this.handleReset} className="btn btn-primary">
              Try Again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
