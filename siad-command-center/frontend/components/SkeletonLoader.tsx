'use client';

import { cn } from '@/lib/utils';

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        'animate-pulse bg-border rounded',
        className
      )}
    />
  );
}

export function CardSkeleton() {
  return (
    <div className="card space-y-4">
      <Skeleton className="h-6 w-48" />
      <div className="space-y-3">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-4 w-5/6" />
      </div>
    </div>
  );
}

export function ChartSkeleton() {
  return (
    <div className="card">
      <Skeleton className="h-6 w-48 mb-4" />
      <Skeleton className="h-[300px] w-full" />
    </div>
  );
}

export function HotspotCardSkeleton() {
  return (
    <div className="card space-y-3">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-16" />
        </div>
        <div className="space-y-1">
          <Skeleton className="h-5 w-16" />
          <Skeleton className="h-5 w-16" />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
    </div>
  );
}

export function ImageSkeleton() {
  return (
    <div className="w-full aspect-square bg-background rounded-lg overflow-hidden">
      <Skeleton className="w-full h-full" />
    </div>
  );
}
