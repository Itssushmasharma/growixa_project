import Image from "next/image";

interface BrandLogoProps {
  width?: number;
  height?: number;
  className?: string;
}

export function BrandLogo({ width = 32, height = 32, className }: BrandLogoProps) {
  return (
    <Image
      src="/assets/logo-icon.png"
      alt="Growixa Logo"
      width={width}
      height={height}
      className={className}
      priority
    />
  );
}
