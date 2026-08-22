import type { ComponentProps, CSSProperties } from 'react';

export type IconSize = 'xxs' | 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'xxl' | 'xxxl';

const sizeMap: Record<IconSize, string> = {
  xxs: 'text-[10px]',
  xs: 'text-[12px]',
  sm: 'text-[14px]',
  md: 'text-[16px]',
  lg: 'text-[18px]',
  xl: 'text-[20px]',
  xxl: 'text-[24px]',
  xxxl: 'text-[48px]',
};

export interface IconProps extends ComponentProps<'span'> {
  name: string;
  filled?: boolean;
  size?: IconSize;
}

export function Icon({ name, filled = false, size = 'md', className, style, ...rest }: IconProps) {
  const merged: CSSProperties = {
    fontVariationSettings: filled ? "'FILL' 1" : "'FILL' 0",
    ...style,
  };
  return (
    <span
      className={`material-symbols-outlined leading-none ${sizeMap[size]} ${className ?? ''}`}
      style={merged}
      {...rest}
    >
      {name}
    </span>
  );
}
