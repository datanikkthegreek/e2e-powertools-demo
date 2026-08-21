import { Button } from "@/components/ui/button";

interface QuantityStepperProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  disabled?: boolean;
  size?: "sm" | "default";
}

export function QuantityStepper({
  value,
  onChange,
  min = 1,
  max,
  disabled = false,
  size = "default",
}: QuantityStepperProps) {
  const dec = () => onChange(Math.max(min, value - 1));
  const inc = () => onChange(max !== undefined ? Math.min(max, value + 1) : value + 1);

  const btnSize = size === "sm" ? "sm" : "icon";
  const widthClass = size === "sm" ? "w-7 h-7" : "";
  const labelWidth = size === "sm" ? "w-6" : "w-8";

  return (
    <div className="flex items-center gap-2">
      <Button
        type="button"
        variant="outline"
        size={btnSize}
        className={widthClass}
        disabled={disabled || value <= min}
        onClick={dec}
        aria-label="Decrease quantity"
      >
        −
      </Button>
      <span className={`${labelWidth} text-center tabular-nums`}>{value}</span>
      <Button
        type="button"
        variant="outline"
        size={btnSize}
        className={widthClass}
        disabled={disabled || (max !== undefined && value >= max)}
        onClick={inc}
        aria-label="Increase quantity"
      >
        +
      </Button>
    </div>
  );
}

export default QuantityStepper;
