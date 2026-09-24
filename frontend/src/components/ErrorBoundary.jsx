import { Component } from "react";

// Error boundaries have no hook equivalent, so this stays a class component.
// Without it a render-time exception blanks the page and the only trace is in
// the console.
export class ErrorBoundary extends Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error("Order Generator crashed:", error, info.componentStack);
  }

  render() {
    if (!this.state.error) {
      return this.props.children;
    }

    return (
      <div className="m-6 max-w-2xl rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
        <h1 className="mb-2 text-base font-semibold">
          The Order Generator hit an unexpected error
        </h1>
        <p className="mb-2">
          Reload the page to try again. The details below are also in the
          browser console.
        </p>
        <pre className="overflow-auto rounded border border-red-200 bg-white p-2 text-xs">
          {this.state.error.message}
        </pre>
      </div>
    );
  }
}
