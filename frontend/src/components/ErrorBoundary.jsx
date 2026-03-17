import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  handleReset = () => {
    this.setState({ hasError: false });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-screen bg-nature p-6 text-center">
          <div className="w-16 h-16 rounded-full bg-amber-100 flex items-center justify-center mb-4">
            <span className="text-2xl text-amber-600 font-bold">!</span>
          </div>
          <h1 className="text-lg font-bold text-gray-700 mb-2">Something went wrong</h1>
          <p className="text-sm text-gray-500 mb-4 max-w-xs">
            The app ran into an unexpected problem. Try refreshing to get back on track.
          </p>
          <button
            onClick={this.handleReset}
            className="px-6 py-2.5 bg-[var(--color-forest)] text-white rounded-full hover:bg-[var(--color-forest-dark)] transition-all font-semibold shadow-sm hover:shadow-md"
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
