import { Link } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { ModeToggle } from "@/components/apx/mode-toggle";
import { AccountPicker } from "./account-picker";

const NAV = [
  { to: "/", label: "Catalog" },
  { to: "/cart", label: "Cart" },
  { to: "/accounts", label: "Accounts" },
  { to: "/purchases", label: "Purchases" },
  { to: "/analytics", label: "Analytics" },
] as const;

export function ShopNavbar() {
  return (
    <header className="z-50 bg-background/80 backdrop-blur-sm border-b">
      <div className="h-16 flex items-center gap-6 px-6">
        <Link to="/" className="flex items-center" aria-label="Bosch home">
          <img
            src="/brand/bosch-logo.png"
            alt="Bosch"
            className="h-10 w-auto"
          />
        </Link>
        <nav className="flex items-center gap-1">
          {NAV.map((item) => (
            <Button key={item.to} variant="ghost" size="sm" asChild>
              <Link
                to={item.to}
                activeProps={{ className: "bg-accent text-accent-foreground" }}
                activeOptions={{ exact: item.to === "/" }}
              >
                {item.label}
              </Link>
            </Button>
          ))}
        </nav>
        <div className="flex-1" />
        <AccountPicker />
        <ModeToggle />
      </div>
    </header>
  );
}

export default ShopNavbar;
