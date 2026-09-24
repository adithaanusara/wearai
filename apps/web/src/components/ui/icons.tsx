import type { SVGProps } from 'react';

type IconProps = SVGProps<SVGSVGElement>;

function Icon({ children, ...props }: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="24"
      height="24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="square"
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  );
}

export const SearchIcon = (props: IconProps) => (
  <Icon {...props}>
    <circle cx="11" cy="11" r="6.5" />
    <path d="M16 16l5 5" />
  </Icon>
);

export const UserIcon = (props: IconProps) => (
  <Icon {...props}>
    <circle cx="12" cy="8" r="4" />
    <path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7" />
  </Icon>
);

export const BagIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M5 8h14l-1 13H6L5 8z" />
    <path d="M9 8V6a3 3 0 016 0v2" />
  </Icon>
);

export const MenuIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M3 6h18M3 12h18M3 18h18" />
  </Icon>
);

export const CloseIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M5 5l14 14M19 5L5 19" />
  </Icon>
);

export const ChevronIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M6 9l6 6 6-6" />
  </Icon>
);

export const InstagramIcon = (props: IconProps) => (
  <Icon {...props}>
    <rect x="4" y="4" width="16" height="16" rx="4" />
    <circle cx="12" cy="12" r="3.5" />
    <circle cx="16.8" cy="7.2" r="0.5" />
  </Icon>
);

export const FacebookIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M14 21v-8h3l.5-3.5H14V7.5c0-1 .5-1.8 1.9-1.8H17.6V2.6C17.3 2.5 16.3 2.4 15.2 2.4 12.7 2.4 10.5 3.9 10.5 7v2.5H7.5V13h3v8" />
  </Icon>
);

export const TikTokIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M14 3v11.5a3.5 3.5 0 11-3.5-3.5" />
    <path d="M14 3c.3 2.5 2 4.2 5 4.5" />
  </Icon>
);

export const YouTubeIcon = (props: IconProps) => (
  <Icon {...props}>
    <rect x="3" y="6" width="18" height="12" rx="3" />
    <path d="M10.5 9.5v5l4.5-2.5z" />
  </Icon>
);
