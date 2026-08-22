import type { ComponentProps } from 'react';
import { cn } from '../../lib/utils';

export function Surface({ className, ...rest }: ComponentProps<'div'>) {
  return <div className={cn('panel-level-1', className)} {...rest} />;
}
