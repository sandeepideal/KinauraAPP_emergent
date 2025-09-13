import React, { Suspense, lazy } from 'react';
import Skeleton from './Skeleton';

// Lazy load recharts components
const LazyLineChart = lazy(() => 
  import('recharts').then(module => ({ 
    default: module.LineChart 
  }))
);

const LazyResponsiveContainer = lazy(() => 
  import('recharts').then(module => ({ 
    default: module.ResponsiveContainer 
  }))
);

const LazyCartesianGrid = lazy(() => 
  import('recharts').then(module => ({ 
    default: module.CartesianGrid 
  }))
);

const LazyXAxis = lazy(() => 
  import('recharts').then(module => ({ 
    default: module.XAxis 
  }))
);

const LazyYAxis = lazy(() => 
  import('recharts').then(module => ({ 
    default: module.YAxis 
  }))
);

const LazyTooltip = lazy(() => 
  import('recharts').then(module => ({ 
    default: module.Tooltip 
  }))
);

const LazyLine = lazy(() => 
  import('recharts').then(module => ({ 
    default: module.Line 
  }))
);

const LazyBarChart = lazy(() => 
  import('recharts').then(module => ({ 
    default: module.BarChart 
  }))
);

const LazyBar = lazy(() => 
  import('recharts').then(module => ({ 
    default: module.Bar 
  }))
);

// Chart Loading Fallback
const ChartSkeleton = ({ height = '256px' }) => (
  <div className="ka-card" style={{ height }}>
    <div className="flex items-center justify-center h-full">
      <Skeleton width="90%" height="80%" />
    </div>
  </div>
);

// Wrapper component for line charts
export const LineChart = ({ data, height = 256, children, ...props }) => (
  <Suspense fallback={<ChartSkeleton height={`${height}px`} />}>
    <LazyResponsiveContainer width="100%" height={height}>
      <LazyLineChart data={data} {...props}>
        <Suspense fallback={null}>
          <LazyCartesianGrid strokeDasharray="3 3" />
          <LazyXAxis dataKey="date" />
          <LazyYAxis />
          <LazyTooltip />
          {children}
        </Suspense>
      </LazyLineChart>
    </LazyResponsiveContainer>
  </Suspense>
);

// Wrapper component for bar charts
export const BarChart = ({ data, height = 256, children, ...props }) => (
  <Suspense fallback={<ChartSkeleton height={`${height}px`} />}>
    <LazyResponsiveContainer width="100%" height={height}>
      <LazyBarChart data={data} {...props}>
        <Suspense fallback={null}>
          <LazyCartesianGrid strokeDasharray="3 3" />
          <LazyXAxis dataKey="date" />
          <LazyYAxis />
          <LazyTooltip />
          {children}
        </Suspense>
      </LazyBarChart>
    </LazyResponsiveContainer>
  </Suspense>
);

// Line component
export const Line = (props) => (
  <Suspense fallback={null}>
    <LazyLine {...props} />
  </Suspense>
);

// Bar component
export const Bar = (props) => (
  <Suspense fallback={null}>
    <LazyBar {...props} />
  </Suspense>
);

// Individual components for more granular control
export const ResponsiveContainer = ({ children, ...props }) => (
  <Suspense fallback={<ChartSkeleton />}>
    <LazyResponsiveContainer {...props}>
      {children}
    </LazyResponsiveContainer>
  </Suspense>
);

export const CartesianGrid = (props) => (
  <Suspense fallback={null}>
    <LazyCartesianGrid {...props} />
  </Suspense>
);

export const XAxis = (props) => (
  <Suspense fallback={null}>
    <LazyXAxis {...props} />
  </Suspense>
);

export const YAxis = (props) => (
  <Suspense fallback={null}>
    <LazyYAxis {...props} />
  </Suspense>
);

export const Tooltip = (props) => (
  <Suspense fallback={null}>
    <LazyTooltip {...props} />
  </Suspense>
);

export default {
  LineChart,
  BarChart,
  Line,
  Bar,
  ResponsiveContainer,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip
};