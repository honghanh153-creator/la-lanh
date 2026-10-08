import { HeartStraight, House, Planet, User } from "@phosphor-icons/react";
import { NavLink } from "react-router-dom";

const items = [
  { to: "/home", label: "Hôm nay", icon: House },
  { to: "/insights", label: "Khám phá", icon: Planet },
  { to: "/radar", label: "Hợp gu", icon: HeartStraight },
  { to: "/profile", label: "Mình", icon: User },
] as const;

export function AppNav() {
  return (
    <nav aria-label="Điều hướng chính" className="app-nav">
      {items.map(({ to, label, icon: Icon }) => (
        <NavLink className={({ isActive }) => isActive ? "app-nav__item app-nav__item--active" : "app-nav__item"} key={to} to={to}>
          {({ isActive }) => <><Icon aria-hidden="true" size={24} weight={isActive ? "fill" : "regular"} /><span>{label}</span></>}
        </NavLink>
      ))}
    </nav>
  );
}
