import type { SVGProps } from "react";

export function BrandLogo(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      width="32"
      height="32"
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <defs>
        <linearGradient
          id="growixaGrad"
          x1="0"
          y1="0"
          x2="32"
          y2="32"
          gradientUnits="userSpaceOnUse"
        >
          <stop offset="0%" stopColor="#2563EB" />
          <stop offset="100%" stopColor="#7C3AED" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="8" fill="url(#growixaGrad)" />
      <path
        d="M16 8C11.5817 8 8 11.5817 8 16C8 20.4183 11.5817 24 16 24C19.5 24 22.4 21.75 23.5 18.6H16V15.4H27.2C27.4 16.2 27.5 17.1 27.5 18C27.5 24.35 22.35 29.5 16 29.5C8.54416 29.5 2.5 23.4558 2.5 16C2.5 8.54416 8.54416 2.5 16 2.5C20.2 2.5 23.9 4.4 26.3 7.4L23.7 10C21.9 7.6 19.1 6 16 6"
        fill="white"
      />
    </svg>
  );
}
